from langchain.agents.middleware import (
    PIIMiddleware,
    ToolRetryMiddleware,
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware
)
from app.agent.exceptions import TimeoutError, ConnectionError
from app.agent.llm_client import get_llm


def should_retry(error: Exception) -> bool:
    """
    Determine if an error should be retried.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if should retry, False otherwise
    """
    if isinstance(error, TimeoutError):
        return True
    if hasattr(error, "status_code"):
        return error.status_code in (429, 503)
    return False


def get_pii_middleware():
    """
    Get PII detection and redaction middleware.
    
    Returns:
        list: List of PII middleware instances
    """
    return [
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",
            strategy="block",
            apply_to_input=True
        ),
    ]


def get_retry_middleware():
    """
    Get retry middleware for tools and models.
    
    Returns:
        list: List of retry middleware instances
    """
    llm = get_llm()
    
    return [
        ToolRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
            max_delay=60.0,
            jitter=True,
            tools=["search"],
            retry_on=(ConnectionError, TimeoutError),
            on_failure="continue"
        ),
        ModelRetryMiddleware(
            max_retries=3,
            retry_on=(TimeoutError, ConnectionError, should_retry),
            backoff_factor=1.5,
            on_failure="continue"
        )
    ]


def get_summarization_middleware():
    """
    Get summarization middleware for long conversations.
    
    Returns:
        SummarizationMiddleware: Configured summarization middleware
    """
    llm = get_llm()
    return SummarizationMiddleware(
        model=llm,
        trigger=("tokens", 4000)
    )


def get_model_call_limit_middleware():
    """
    Get model call limit middleware.
    
    Returns:
        ModelCallLimitMiddleware: Configured model call limit middleware
    """
    return ModelCallLimitMiddleware(
        thread_limit=20,
        run_limit=3,
        exit_behavior="end"
    )


def get_tool_call_limit_middleware():
    """
    Get tool call limit middleware.
    
    Returns:
        ToolCallLimitMiddleware: Configured tool call limit middleware
    """
    return ToolCallLimitMiddleware(
        tool_name="search",
        thread_limit=20,
        run_limit=2
    )