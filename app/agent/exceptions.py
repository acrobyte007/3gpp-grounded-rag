# app/agent/exceptions.py

class RetryableToolError(RuntimeError):
    """Temporary error. Agent may retry."""
    pass


class NonRetryableToolError(ValueError):
    """Bad input. Agent should not retry."""
    pass


class TimeoutError(Exception):
    """Custom exception for timeout errors."""
    pass


class ConnectionError(Exception):
    """Custom exception for connection errors."""
    pass


class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""
    pass


class ValidationError(Exception):
    """Exception for validation errors."""
    pass