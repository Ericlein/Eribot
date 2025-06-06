"""
Custom exceptions for EriBot
"""

from typing import Optional, Dict, Any


class ErioBotException(Exception):
    """Base exception for all EriBot errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(ErioBotException):
    """Raised when configuration is invalid or missing"""


class SlackError(ErioBotException):
    """Raised when Slack integration fails"""


class RemediationError(ErioBotException):
    """Raised when remediation actions fail"""


class MonitoringError(ErioBotException):
    """Raised when system monitoring fails"""


class ValidationError(ErioBotException):
    """Raised when input validation fails"""


class NetworkError(ErioBotException):
    """Raised when network operations fail"""


class ServiceUnavailableError(ErioBotException):
    """Raised when a required service is unavailable"""


class ThresholdExceededError(ErioBotException):
    """Raised when system metrics exceed configured thresholds"""

    def __init__(
        self,
        metric: str,
        current_value: float,
        threshold: float,
        message: Optional[str] = None,
    ):
        self.metric = metric
        self.current_value = current_value
        self.threshold = threshold

        if not message:
            message = f"{metric} threshold exceeded: {current_value}% > {threshold}%"

        super().__init__(
            message,
            details={
                "metric": metric,
                "current_value": current_value,
                "threshold": threshold,
                "exceeded_by": current_value - threshold,
            },
        )


class RateLimitError(ErioBotException):
    """Raised when rate limits are exceeded"""

    def __init__(self, service: str, retry_after: Optional[int] = None):
        self.service = service
        self.retry_after = retry_after

        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(message, details={"service": service, "retry_after": retry_after})


class AuthenticationError(ErioBotException):
    """Raised when authentication fails"""


class PermissionError(ErioBotException):
    """Raised when insufficient permissions are detected"""


class SystemResourceError(ErioBotException):
    """Raised when system resources are unavailable or exhausted"""

    def __init__(self, resource: str, message: Optional[str] = None):
        self.resource = resource

        if not message:
            message = f"System resource unavailable: {resource}"

        super().__init__(message, details={"resource": resource})


class TimeoutError(ErioBotException):
    """Raised when operations timeout"""

    def __init__(self, operation: str, timeout_seconds: float):
        self.operation = operation
        self.timeout_seconds = timeout_seconds

        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"

        super().__init__(
            message,
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )


class DataError(ErioBotException):
    """Raised when data is invalid or corrupted"""


class DependencyError(ErioBotException):
    """Raised when external dependencies fail"""

    def __init__(self, dependency: str, message: Optional[str] = None):
        self.dependency = dependency

        if not message:
            message = f"Dependency failure: {dependency}"

        super().__init__(message, details={"dependency": dependency})


# Convenience functions for common error scenarios


def raise_config_error(setting: str, value: Any = None, expected: str = ""):
    """Raise a configuration error with standardized message"""
    details = {"setting": setting}
    if value is not None:
        details["value"] = value
    if expected:
        details["expected"] = expected

    message = f"Invalid configuration for '{setting}'"
    if expected:
        message += f". Expected: {expected}"
    if value is not None:
        message += f". Got: {value}"

    raise ConfigurationError(message, details)


def raise_threshold_error(metric: str, current: float, threshold: float):
    """Raise a threshold exceeded error"""
    raise ThresholdExceededError(metric, current, threshold)


def raise_slack_error(operation: str, error: str):
    """Raise a Slack error with operation context"""
    raise SlackError(
        f"Slack {operation} failed: {error}",
        details={"operation": operation, "error": error},
    )


def raise_remediation_error(action: str, error: str):
    """Raise a remediation error with action context"""
    raise RemediationError(
        f"Remediation action '{action}' failed: {error}",
        details={"action": action, "error": error},
    )


def handle_exception(func):
    """Decorator to convert common exceptions to EriBot exceptions"""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ErioBotException:
            # Re-raise EriBot exceptions as-is
            raise
        except ConnectionError as e:
            raise NetworkError(f"Network connection failed: {e}")
        except FileNotFoundError as e:
            raise ConfigurationError(f"Required file not found: {e}")
        except PermissionError as e:
            raise PermissionError(f"Insufficient permissions: {e}")
        except ValueError as e:
            raise ValidationError(f"Invalid value: {e}")
        except Exception as e:
            # Convert unexpected exceptions
            raise ErioBotException(f"Unexpected error in {func.__name__}: {e}")

    return wrapper
