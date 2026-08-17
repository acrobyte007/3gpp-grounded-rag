from typing import List, Dict
from langchain.tools import tool, ToolRuntime
from app.agent.schemas import UserContext
from app.agent.exceptions import RetryableToolError, NonRetryableToolError, TimeoutError, ConnectionError
from app.services.embeddings import embedding_service
from app.database.pincone_db import pinecone_service
from logger.logger import get_logger

logger = get_logger(__name__)


async def vector_search(
    namespace: str,
    query: str,
    doc_ids: List[str],
    top_k: int = 5
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
                "document_id": results["chunk_ids"][i].split("#")[0] if results["chunk_ids"][i] else "",
                "chunk_number": i + 1,
                "score": 0,
                "language": results["lang_list"][i] if i < len(results["lang_list"]) else "en"
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
) -> List[Dict]:
    """
    Perform vector similarity search on Pinecone index.
    
    Args:
        namespace: User namespace for isolation
        query: Search query string
        doc_ids: List of document IDs to filter results
        top_k: Number of results to return per document
    
    Returns:
        List of dictionaries containing chunk text, document ID, chunk number, score, and language
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
            top_k=5
        )

        if chunks is None:
            raise RetryableToolError("Retriever returned None.")

        logger.info(
            "Retrieved %d chunks | namespace=%s | doc_ids=%s",
            len(chunks),
            context.namespace,
            context.doc_ids,
        )

        return chunks

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