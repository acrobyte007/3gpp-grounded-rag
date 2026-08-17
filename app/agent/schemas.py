
class RetryableToolError(RuntimeError):
    """Temporary error. Agent may retry."""

class NonRetryableToolError(ValueError):
    """Bad input. Agent should not retry."""

class TimeoutError(Exception):
    """Custom exception for timeout errors."""
    pass

class ConnectionError(Exception):
    """Custom exception for connection errors."""
    pass
