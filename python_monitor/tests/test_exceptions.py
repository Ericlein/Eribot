import pytest
from utils.exceptions import (
    ConfigurationError,
    SlackError,
    RemediationError,
    ThresholdExceededError,
)


@pytest.mark.unit
def test_configuration_error():
    """Test ConfigurationError creation"""
    error = ConfigurationError("Test error", {"key": "value"})
    assert str(error) == "Test error - Details: {'key': 'value'}"


@pytest.mark.unit
def test_threshold_exceeded_error():
    """Test ThresholdExceededError"""
    error = ThresholdExceededError("CPU", 95.0, 90.0)
    assert error.metric == "CPU"
    assert error.current_value == 95.0
    assert error.threshold == 90.0
