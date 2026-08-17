from typing import List, Dict
from langchain.tools import tool, ToolRuntime
from app.agent.schemas import UserContext
from app.agent.exceptions import RetryableToolError, NonRetryableToolError, TimeoutError, ConnectionError
from app.services.embeddings import embedding_service
from app.database.pincone_db import pinecone_service
from logger.logger import get_logger
import math
from collections import Counter

logger = get_logger(__name__)


class BM25Reranker:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.avgdl = 0
        self.doc_freqs = {}
        self.doc_len = []
        self.total_docs = 0

    def fit(self, corpus: List[List[str]]):
        self.total_docs = len(corpus)
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_len) / self.total_docs
        
        for doc in corpus:
            doc_counter = Counter(doc)
            for term in doc_counter:
                if term not in self.doc_freqs:
                    self.doc_freqs[term] = 0
                self.doc_freqs[term] += 1

    def score(self, query: List[str], doc: List[str]) -> float:
        score = 0.0
        doc_len = len(doc)
        doc_counter = Counter(doc)
        
        for term in query:
            if term not in self.doc_freqs:
                continue
            
            tf = doc_counter.get(term, 0)
            if tf == 0:
                continue
            
            idf = math.log(
                (self.total_docs - self.doc_freqs[term] + 0.5) /
                (self.doc_freqs[term] + 0.5) + 1.0
            )
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            
            score += idf * (numerator / denominator)
        
        return score

    def rerank(self, query: List[str], candidates: List[Dict]) -> List[Dict]:
        if not candidates:
            return []
        
        corpus = []
        valid_candidates = []
        
        for candidate in candidates:
            tokens = candidate.get("tokens", [])
            if tokens:
                corpus.append(tokens)
                valid_candidates.append(candidate)
        
        if not corpus:
            return []
        
        self.fit(corpus)
        
        scored_candidates = []
        for i, doc in enumerate(corpus):
            score = self.score(query, doc)
            scored_candidates.append({
                **valid_candidates[i],
                "bm25_score": score
            })
        
        reranked = sorted(
            scored_candidates,
            key=lambda x: x.get("bm25_score", 0),
            reverse=True
        )
        
        return reranked


async def vector_search(
    namespace: str,
    query: str,
    doc_ids: List[str],
    top_k: int = 30
) -> List[Dict]:
    try:
        embedding_result = embedding_service.embed([query])
        query_vector = embedding_result[0]["embedding"]
        
        results = pinecone_service.search(
            namespace=namespace,
            vector=query_vector,
            doc_ids=doc_ids,
            top_k=top_k
        )
        
        if not results or not results.get("chunk_texts"):
            return []
        
        chunks = []
        for i in range(len(results["chunk_texts"])):
            chunks.append({
                "text": results["chunk_texts"][i],
                "tokens": results["tokens_list"][i] if i < len(results["tokens_list"]) else []
            })
        
        return chunks
        
    except TimeoutError as e:
        logger.error(f"Vector search timed out: {str(e)}")
        raise
    except ConnectionError as e:
        logger.error(f"Vector search connection failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}", exc_info=True)
        raise


@tool
async def search(
    runtime: ToolRuntime[UserContext],
    query: str,
) -> str:
    """
    Args:
        query: Search query string
    Returns:
        List of dictionaries containing chunk text, document ID, chunk number, language, and tokens
    """
    if runtime is None:
        raise NonRetryableToolError("runtime cannot be None.")

    if not isinstance(query, str) or not query.strip():
        raise NonRetryableToolError("query must be a non-empty string.")

    context = runtime.context

    if context is None:
        raise RetryableToolError("Runtime context is missing.")

    if not context.namespace:
        raise NonRetryableToolError("namespace is missing.")

    if not context.doc_ids:
        raise NonRetryableToolError("doc_ids is missing.")

    try:
        chunks = await vector_search(
            namespace=context.namespace,
            query=query,
            doc_ids=context.doc_ids,
            top_k=30
        )

        if not chunks:
            logger.warning("No relevant chunks found in the knowledge base.")
            return "No relevant information found in the documents."

        query_tokens = embedding_service.tokenize_sentences(query)[0]
        logger.info("Tokenized query: %s", query_tokens)
        reranker = BM25Reranker()
        reranked_chunks = reranker.rerank(query_tokens, chunks)
        
        top_chunks = reranked_chunks[:10]

        logger.info(
            "Retrieved %d chunks, reranked to %d | namespace=%s | doc_ids=%s",
            len(chunks),
            len(top_chunks),
            context.namespace,
            context.doc_ids,
        )

        return top_chunks

    except TimeoutError as e:
        logger.exception("Retrieval timed out.")
        raise RetryableToolError("Temporary retrieval timeout. Please retry.") from e

    except ConnectionError as e:
        logger.exception("Retriever connection failed.")
        raise RetryableToolError("Temporary retrieval connection failure. Please retry.") from e

    except Exception as e:
        logger.exception("Unexpected error during retrieval.")
        raise RetryableToolError(f"Search tool failed: {type(e).__name__}: {e}") from e


tools = [search]