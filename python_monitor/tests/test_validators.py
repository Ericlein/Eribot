"""
Tests for validators module
"""

import pytest

from python_monitor.utils.validators import (
    validate_slack_token,
    validate_slack_channel,
    validate_threshold,
    validate_url,
    validate_hostname,
)

from python_monitor.utils.exceptions import ValidationError


class TestBasicValidators:
    """Test basic validation functions"""

    def test_validate_slack_token_valid(self):
        """Test valid Slack token validation"""
        valid_tokens = [
            "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx",
            "xoxb-1234567890123-1234567890123-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
        ]

        for token in valid_tokens:
            assert validate_slack_token(token) is True

    def test_validate_slack_token_invalid(self):
        """Test invalid Slack token validation"""
        invalid_tokens = [
            "",
            "invalid-token",
            "xoxp-123456789-123456789-abcdefghijklmnopqrstuvwx",  # Wrong prefix
            "xoxb-123-456-abc",  # Wrong format
            "xoxb-not-numeric-part-abcdef",
        ]

        for token in invalid_tokens:
            with pytest.raises(ValidationError):
                validate_slack_token(token)

    def test_validate_slack_channel_valid(self):
        """Test valid Slack channel validation"""
        valid_channels = [
            "#general",
            "#dev-alerts",
            "#test_channel",
            "#a",
            "#alerts-123",
            "#very-long-channel-name",
            "#very-very-long-channel-name-that-is-under-80-chars",
        ]

        for channel in valid_channels:
            assert validate_slack_channel(channel) is True

    def test_validate_slack_channel_invalid(self):
        """Test invalid Slack channel validation"""
        invalid_channels = [
            "",
            "general",  # Missing #
            "#General",  # Capital letters
            "#test channel",  # Space
            "#test@channel",  # Invalid character
            "#" + "a" * 81,  # Too long (81 characters after #)
        ]

        for channel in invalid_channels:
            with pytest.raises(ValidationError):
                validate_slack_channel(channel)

    def test_validate_threshold_valid(self):
        """Test valid threshold validation"""
        valid_thresholds = [0, 50, 85.5, 100, 99.99]

        for threshold in valid_thresholds:
            assert validate_threshold(threshold) is True

    def test_validate_threshold_invalid(self):
        """Test invalid threshold validation"""
        invalid_thresholds = [-1, 101, 150, "85", None]

        for threshold in invalid_thresholds:
            with pytest.raises(ValidationError):
                validate_threshold(threshold)

    def test_validate_threshold_custom_range(self):
        """Test threshold validation with custom range"""
        assert validate_threshold(50, min_val=0, max_val=200) is True
        assert validate_threshold(150, min_val=0, max_val=200) is True

        with pytest.raises(ValidationError):
            validate_threshold(250, min_val=0, max_val=200)

    def test_validate_url_valid(self):
        """Test valid URL validation"""
        valid_urls = [
            "http://localhost:5001",
            "https://api.slack.com",
            "http://192.168.1.1:8080/health",
            "https://example.com/path?param=value",
        ]

        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        invalid_urls = [
            "",
            "localhost:5001",  # Missing scheme
            "ftp://example.com",  # Wrong scheme
            "http://",  # Missing netloc
            "not-a-url",
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                validate_url(url)

    def test_validate_hostname_valid(self):
        """Test valid hostname validation"""
        valid_hostnames = [
            "localhost",
            "example.com",
            "sub.example.com",
            "server-01",
            "192.168.1.1",  # IP addresses are valid hostnames
        ]

        for hostname in valid_hostnames:
            result = validate_hostname(hostname)
            assert result is True, f"Expected True for hostname '{hostname}', got {result}"

    def test_validate_hostname_invalid(self):
        """Test invalid hostname validation"""
        invalid_hostnames = [
            "",
            "host_with_underscore",
            "host..double.dot",
            "a" * 254,  # Too long
            "-starting-with-dash",
        ]

        for hostname in invalid_hostnames:
            with pytest.raises(ValidationError, match=r".*"):
                validate_hostname(hostname)


@pytest.fixture
def validator():
    """Create a validator instance for testing"""

    # You'll need to import and create your ConfigValidator class here
    class MockValidator:
        def __init__(self):
            self.errors = []

        def get_errors(self):
            return self.errors

        def clear_errors(self):
            self.errors = []

        def validate_slack_config(self, config):
            try:
                if "channel" in config:
                    validate_slack_channel(config["channel"])
                if "token" in config:
                    validate_slack_token(config["token"])
                return True
            except ValidationError as e:
                self.errors.append(f"Slack config error: {str(e)}")
                return False

        def validate_monitoring_config(self, config):
            try:
                if "cpu_threshold" in config:
                    validate_threshold(config["cpu_threshold"])
                if "disk_threshold" in config:
                    validate_threshold(config["disk_threshold"])
                if "memory_threshold" in config:
                    validate_threshold(config["memory_threshold"])
                if "check_interval" in config:
                    if (
                        not isinstance(config["check_interval"], (int, float))
                        or config["check_interval"] <= 0
                    ):
                        raise ValidationError("Check interval must be positive")
                return True
            except ValidationError as e:
                self.errors.append(f"Monitoring config error: {str(e)}")
                return False

        def validate_remediator_config(self, config):
            try:
                if "url" in config:
                    validate_url(config["url"])
                if "timeout" in config:
                    if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
                        raise ValidationError("Timeout must be positive")
                return True
            except ValidationError as e:
                self.errors.append(f"Remediator config error: {str(e)}")
                return False

        def validate_full_config(self, config):
            self.clear_errors()
            valid = True

            if "monitoring" in config:
                if not self.validate_monitoring_config(config["monitoring"]):
                    valid = False

            if "slack" in config:
                if not self.validate_slack_config(config["slack"]):
                    valid = False

            if "remediator" in config:
                if not self.validate_remediator_config(config["remediator"]):
                    valid = False

            return valid

    return MockValidator()


class TestConfigValidator:
    """Test configuration validator class methods"""

    def test_validate_slack_config_valid(self, validator):
        """Test valid Slack configuration validation"""
        config = {
            "channel": "#test-alerts",
            "token": "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx",
        }

        assert validator.validate_slack_config(config) is True
        assert len(validator.get_errors()) == 0

    def test_validate_slack_config_invalid_channel(self, validator):
        """Test Slack configuration with invalid channel"""
        config = {
            "channel": "invalid-channel",  # Missing #
            "token": "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx",
        }

        assert validator.validate_slack_config(config) is False
        errors = validator.get_errors()
        assert len(errors) > 0
        assert "Slack config" in errors[0]

    def test_validate_monitoring_config_valid(self, validator):
        """Test valid monitoring configuration validation"""
        config = {
            "cpu_threshold": 90,
            "disk_threshold": 90,
            "check_interval": 60,
            "memory_threshold": 85,
        }

        assert validator.validate_monitoring_config(config) is True
        assert len(validator.get_errors()) == 0

    def test_validate_monitoring_config_invalid_threshold(self, validator):
        """Test monitoring configuration with invalid threshold"""
        config = {
            "cpu_threshold": 150,  # Invalid: > 100
            "disk_threshold": 90,
            "check_interval": 60,
        }

        assert validator.validate_monitoring_config(config) is False
        errors = validator.get_errors()
        assert len(errors) > 0

    def test_validate_remediator_config_valid(self, validator):
        """Test valid remediator configuration validation"""
        config = {"url": "http://localhost:5001", "timeout": 30}

        assert validator.validate_remediator_config(config) is True
        assert len(validator.get_errors()) == 0

    def test_validate_full_config_valid(self, validator):
        """Test full configuration validation"""
        config = {
            "monitoring": {
                "cpu_threshold": 90,
                "disk_threshold": 90,
                "check_interval": 60,
            },
            "slack": {"channel": "#test-alerts"},
            "remediator": {"url": "http://localhost:5001"},
        }

        assert validator.validate_full_config(config) is True
        assert len(validator.get_errors()) == 0

    def test_validate_full_config_multiple_errors(self, validator):
        """Test full configuration validation with multiple errors"""
        config = {
            "monitoring": {
                "cpu_threshold": 150,  # Invalid
                "disk_threshold": 90,
                "check_interval": 60,
            },
            "slack": {"channel": "invalid-channel"},  # Invalid
            "remediator": {"url": "invalid-url"},  # Invalid
        }

        assert validator.validate_full_config(config) is False
        errors = validator.get_errors()
        assert len(errors) >= 3  # Should have multiple errors
