from langchain.tools import tool,ToolRuntime
from typing import Dict
from agent.schemas import UserContext, NonRetryableToolError, RetryableToolError
from logger.logger import get_logger
logger = get_logger(__name__)


@tool
async def search(
    runtime: ToolRuntime[UserContext],
    query: str,
    translated_queries: Dict[str, str],
):
    """
    Search the knowledge base.

    Args:
        query: User's original query.
        translated_queries: Dictionary containing translated queries.
            Example:
            {
                "en": "...",
                "hi": "...",
                "bn": "..."
            }

    Returns:
        List of retrieved chunks.
    """

    if runtime is None:
        raise NonRetryableToolError("runtime cannot be None.")

    if not isinstance(query, str) or not query.strip():
        raise NonRetryableToolError("query must be a non-empty string.")

    if not isinstance(translated_queries, dict):
        raise NonRetryableToolError("translated_queries must be a dictionary.")

    required_languages = {"en", "hi", "bn"}

    missing = required_languages - translated_queries.keys()
    if missing:
        raise NonRetryableToolError(
            f"translated_queries is missing required languages: {sorted(missing)}"
        )

    for lang in required_languages:
        value = translated_queries.get(lang)

        if not isinstance(value, str):
            raise NonRetryableToolError(
                f"translated_queries['{lang}'] must be a string."
            )

        if not value.strip():
            raise NonRetryableToolError(
                f"translated_queries['{lang}'] cannot be empty."
            )

    context = runtime.context

    if context is None:
        raise RetryableToolError("Runtime context is missing.")

    if not context.namespace:
        raise NonRetryableToolError("namespace is missing.")

    if not context.doc_ids:
        raise NonRetryableToolError("doc_ids is missing.")

    try:
        chunks = await top_k_retrieval(
            context.namespace,
            query,
            context.doc_ids,
            translated_queries,
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
        raise RetryableToolError(
            "Temporary retrieval timeout. Please retry."
        ) from e

    except ConnectionError as e:
        logger.exception("Retriever connection failed.")
        raise RetryableToolError(
            "Temporary retrieval connection failure. Please retry."
        ) from e

    except Exception as e:
        logger.exception("Unexpected error during retrieval.")
        raise RetryableToolError(
            f"Search tool failed: {type(e).__name__}: {e}"
        ) from e

tools = [search]