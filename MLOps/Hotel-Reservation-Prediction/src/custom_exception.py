"""
custom_exception.py
===================
Industry-Standard Custom Exception Handling Module for Production Python, MLOps, 
AI Engineering, and Microservice Architecture.

Key Features:
- Base Custom Exception class with detailed stack trace extraction (file, line, function).
- Structured context payload and JSON serialization (`to_dict()`) for APM/logging (Datadog, Sentry, CloudWatch).
- HTTP Status Code mapping for REST APIs (FastAPI, Flask, Django).
- Domain-specific exception hierarchy (Validation, Auth, Database, Model/LLM, External API).
- Helper function for formatting tracebacks.
- Exception handler decorator for clean exception wrapping.
"""

from datetime import datetime, timezone
import inspect
import sys
from typing import Any, Dict, Optional, Type, Union


def _extract_stack_frame(error_detail: Optional[Any] = sys):
    """
    Extracts stack frame details (file_name, line_number, function_name)
    from sys.exc_info() or by walking back the call stack.
    """
    exc_tb = None
    if hasattr(error_detail, "exc_info"):
        _, _, exc_tb = error_detail.exc_info()
    elif isinstance(error_detail, tuple) and len(error_detail) == 3:
        _, _, exc_tb = error_detail

    if exc_tb is not None:
        frame = exc_tb.tb_frame
        return (
            frame.f_code.co_filename,
            exc_tb.tb_lineno,
            frame.f_code.co_name
        )

    # Fallback frame inspection when sys.exc_info() is empty
    try:
        current_frame = inspect.currentframe()
        if current_frame:
            frame = current_frame.f_back
            internal_funcs = {
                "_extract_stack_frame",
                "get_detailed_error_message",
                "__init__",
            }
            while frame:
                is_internal = frame.f_code.co_name in internal_funcs
                if not is_internal:
                    return (
                        frame.f_code.co_filename,
                        frame.f_lineno,
                        frame.f_code.co_name,
                    )
                frame = frame.f_back
    except Exception:
        pass

    return ("Unknown", 0, "Unknown")


def get_detailed_error_message(
    error: Union[Exception, str],
    error_detail: Optional[Any] = sys
) -> str:
    """
    Extracts detailed error information including file name, line number, and function name.

    Args:
        error (Union[Exception, str]): The exception instance or string message.
        error_detail (Optional[Any]): The sys module or sys.exc_info() tuple.

    Returns:
        str: Standardized formatted error string with exact file and line trace.
    """
    file_name, line_number, func_name = _extract_stack_frame(error_detail)
    if file_name != "Unknown":
        return f"Error in [{file_name}] at line [{line_number}] in function [{func_name}]: {str(error)}"
    return f"Error: {str(error)}"


class CustomException(Exception):
    """
    Industry Standard Base Exception Class for Enterprise Applications.

    Attributes:
        raw_message (str): Plain text message of the error.
        detailed_message (str): Error message augmented with line number and file trace.
        error_code (str): Machine-readable string code (e.g., 'VALIDATION_ERROR').
        status_code (int): Corresponding HTTP status code (e.g., 400, 404, 500).
        details (Dict[str, Any]): Additional context/metadata dictionary.
        timestamp (str): UTC ISO-8601 timestamp of when the exception occurred.
        file_name (str): File where error was triggered.
        line_number (int): Line number where error occurred.
        function_name (str): Function name where error was triggered.
    """

    default_status_code: int = 500
    default_error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        error_message: Union[Exception, str],
        error_detail: Optional[Any] = sys,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        raw_msg = str(error_message)
        super().__init__(raw_msg)
        
        self.raw_message: str = raw_msg
        self.error_detail = error_detail
        self.detailed_message: str = get_detailed_error_message(raw_msg, error_detail)
        
        self.error_code: str = error_code or self.default_error_code
        self.status_code: int = status_code or self.default_status_code
        self.details: Dict[str, Any] = details or {}
        self.timestamp: str = datetime.now(timezone.utc).isoformat()

        # Extract file & line metadata for structured logging
        self.file_name, self.line_number, self.function_name = _extract_stack_frame(error_detail)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the exception into a JSON-compatible dictionary for API responses and loggers.
        """
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.raw_message,
                "detailed_message": self.detailed_message,
                "status_code": self.status_code,
                "timestamp": self.timestamp,
                "trace": {
                    "file": self.file_name,
                    "line": self.line_number,
                    "function": self.function_name,
                },
                "context": self.details,
            }
        }

    def __str__(self) -> str:
        return self.detailed_message

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(code='{self.error_code}', "
            f"status={self.status_code}, message='{self.raw_message}')>"
        )


# =====================================================================
# Domain-Specific Exception Hierarchy
# =====================================================================

class DataValidationError(CustomException):
    """Raised when input data validation fails."""
    default_status_code = 400
    default_error_code = "VALIDATION_ERROR"


class ResourceNotFoundError(CustomException):
    """Raised when a requested resource or entity is not found."""
    default_status_code = 404
    default_error_code = "RESOURCE_NOT_FOUND"


class AuthenticationError(CustomException):
    """Raised when user authentication fails."""
    default_status_code = 401
    default_error_code = "UNAUTHENTICATED"


class AuthorizationError(CustomException):
    """Raised when a user lacks required permissions."""
    default_status_code = 403
    default_error_code = "PERMISSION_DENIED"


class ConfigurationError(CustomException):
    """Raised when application environment or configuration is missing/invalid."""
    default_status_code = 500
    default_error_code = "CONFIG_ERROR"


class DatabaseError(CustomException):
    """Raised when database query or connection operations fail."""
    default_status_code = 500
    default_error_code = "DATABASE_ERROR"


class ExternalAPIError(CustomException):
    """Raised when downstream external service/API calls fail."""
    default_status_code = 502
    default_error_code = "EXTERNAL_API_ERROR"


class ModelInferenceError(CustomException):
    """Raised when ML/AI model inference or LLM processing fails."""
    default_status_code = 500
    default_error_code = "MODEL_INFERENCE_ERROR"


class RateLimitExceededError(CustomException):
    """Raised when API rate limit or quota is exceeded."""
    default_status_code = 429
    default_error_code = "RATE_LIMIT_EXCEEDED"


# =====================================================================
# Decorator Utility
# =====================================================================

def handle_custom_exception(
    wrapper_exception: Type[CustomException] = CustomException,
    default_message: str = "An unexpected error occurred during execution."
):
    """
    Decorator to wrap function calls and automatically capture unhandled exceptions
    as structured CustomExceptions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CustomException:
                raise
            except Exception as e:
                raise wrapper_exception(
                    error_message=f"{default_message} Original error: {str(e)}",
                    error_detail=sys,
                    details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
                ) from e
        return wrapper
    return decorator
