"""
Tests for custom exceptions
"""

import pytest

from utils.exceptions import (
    ErioBotException,
    ConfigurationError,
    SlackError,
    RemediationError,
    ThresholdExceededError,
    RateLimitError,
    AuthenticationError,
    TimeoutError as EriTimeoutError,
    NetworkError,
    ServiceUnavailableError,
    ValidationError,
    MonitoringError,
)


class TestExceptions:
    """Test custom exception classes"""

    @pytest.mark.unit
    def test_eribot_exception_basic(self):
        """Test basic ErioBotException"""
        error = ErioBotException("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    @pytest.mark.unit
    def test_eribot_exception_with_details(self):
        """Test ErioBotException with details"""
        details = {"key": "value", "number": 42}
        error = ErioBotException("Test error", details)
        assert "Test error" in str(error)
        assert "Details:" in str(error)
        assert error.details == details

    @pytest.mark.unit
    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Config missing")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Config missing"

    @pytest.mark.unit
    def test_slack_error(self):
        """Test SlackError"""
        error = SlackError("Slack API failed")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Slack API failed"

    @pytest.mark.unit
    def test_remediation_error(self):
        """Test RemediationError"""
        error = RemediationError("Remediation failed")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Remediation failed"

    @pytest.mark.unit
    def test_threshold_exceeded_error(self):
        """Test ThresholdExceededError"""
        error = ThresholdExceededError("CPU", 95.0, 90.0)
        assert isinstance(error, ErioBotException)
        assert error.metric == "CPU"
        assert error.current_value == 95.0
        assert error.threshold == 90.0
        assert "CPU threshold exceeded" in str(error)
        assert error.details["exceeded_by"] == 5.0

    @pytest.mark.unit
    def test_threshold_exceeded_error_custom_message(self):
        """Test ThresholdExceededError with custom message"""
        error = ThresholdExceededError("Memory", 85.0, 80.0, "Custom message")
        assert error.metric == "Memory"
        assert error.current_value == 85.0
        assert error.threshold == 80.0
        # The custom message should be in the string representation
        assert "Custom message" in str(error)
        # But details should still be populated
        assert error.details["exceeded_by"] == 5.0

    @pytest.mark.unit
    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError("slack", 60)
        assert isinstance(error, ErioBotException)
        assert error.service == "slack"
        assert error.retry_after == 60
        assert "Rate limit exceeded for slack" in str(error)
        assert "Retry after 60 seconds" in str(error)

    @pytest.mark.unit
    def test_rate_limit_error_no_retry_after(self):
        """Test RateLimitError without retry_after"""
        error = RateLimitError("api")
        assert error.service == "api"
        assert error.retry_after is None
        assert "Rate limit exceeded for api" in str(error)
        assert "Retry after" not in str(error)

    @pytest.mark.unit
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Invalid token")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Invalid token"

    @pytest.mark.unit
    def test_timeout_error(self):
        """Test TimeoutError"""
        error = EriTimeoutError("API call", 30.0)
        assert isinstance(error, ErioBotException)
        assert error.operation == "API call"
        assert error.timeout_seconds == 30.0
        assert "API call" in str(error)
        assert "30.0 seconds" in str(error)

    @pytest.mark.unit
    def test_network_error(self):
        """Test NetworkError"""
        error = NetworkError("Connection failed")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Connection failed"

    @pytest.mark.unit
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError"""
        error = ServiceUnavailableError("Service down")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Service down"

    @pytest.mark.unit
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Invalid input"

    @pytest.mark.unit
    def test_monitoring_error(self):
        """Test MonitoringError"""
        error = MonitoringError("Monitor failed")
        assert isinstance(error, ErioBotException)
        assert str(error) == "Monitor failed"

    # Additional tests to improve coverage
    @pytest.mark.unit
    def test_error_helper_functions(self):
        """Test error helper functions"""
        from utils.exceptions import (
            raise_config_error,
            raise_threshold_error,
            raise_slack_error,
            raise_remediation_error,
        )

        # Test raise_config_error
        with pytest.raises(ConfigurationError):
            raise_config_error("test_setting", "invalid_value", "valid_format")

        # Test raise_threshold_error
        with pytest.raises(ThresholdExceededError):
            raise_threshold_error("CPU", 95.0, 90.0)

        # Test raise_slack_error
        with pytest.raises(SlackError):
            raise_slack_error("send_message", "API error")

        # Test raise_remediation_error
        with pytest.raises(RemediationError):
            raise_remediation_error("high_cpu", "Service unavailable")

    @pytest.mark.unit
    def test_handle_exception_decorator(self):
        """Test handle_exception decorator"""
        from utils.exceptions import handle_exception

        @handle_exception
        def test_function_success():
            return "success"

        @handle_exception
        def test_function_connection_error():
            raise ConnectionError("Network issue")

        @handle_exception
        def test_function_file_not_found():
            raise FileNotFoundError("File missing")

        @handle_exception
        def test_function_permission_error():
            raise PermissionError("Access denied")

        @handle_exception
        def test_function_value_error():
            raise ValueError("Invalid value")

        @handle_exception
        def test_function_generic_error():
            raise RuntimeError("Generic error")

        # Test successful execution
        assert test_function_success() == "success"

        # Test error conversions
        with pytest.raises(NetworkError):
            test_function_connection_error()

        with pytest.raises(ConfigurationError):
            test_function_file_not_found()

        with pytest.raises(ErioBotException):
            test_function_generic_error()
