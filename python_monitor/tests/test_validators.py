"""
Simple unit tests for validators - replaces test_validators.py
python_monitor/tests/test_validators.py
"""

import pytest
from python_monitor.utils.validators import (
    validate_slack_token,
    validate_slack_channel,
    validate_threshold,
    validate_url,
    validate_hostname,
    validate_config_section,
    validate_complete_config,
)
from python_monitor.utils.exceptions import ValidationError


@pytest.mark.unit
class TestValidators:
    """Unit tests for all validator functions"""

    # Slack Token Tests
    def test_validate_slack_token_valid(self):
        """Test valid Slack token validation"""
        valid_tokens = [
            "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx",
            "xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx",
        ]
        for token in valid_tokens:
            assert validate_slack_token(token) is True

    def test_validate_slack_token_invalid_empty(self):
        """Test empty Slack token raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack token cannot be empty"):
            validate_slack_token("")

    def test_validate_slack_token_invalid_type(self):
        """Test non-string Slack token raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack token must be a string"):
            validate_slack_token(123)

    def test_validate_slack_token_invalid_prefix(self):
        """Test invalid Slack token prefix raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid Slack token format"):
            validate_slack_token("xoxp-123456789-123456789-abcdefghijklmnopqrstuvwx")

    def test_validate_slack_token_invalid_format(self):
        """Test malformed Slack token raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid Slack token format"):
            validate_slack_token("xoxb-invalid-format")

    def test_validate_slack_token_non_numeric_parts(self):
        """Test Slack token with non-numeric parts raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid Slack token format"):
            validate_slack_token("xoxb-abc-def-abcdefghijklmnopqrstuvwx")

    def test_validate_slack_token_short_secret(self):
        """Test Slack token with short secret raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid Slack token format"):
            validate_slack_token("xoxb-123456789-123456789-short")

    # Slack Channel Tests
    def test_validate_slack_channel_valid(self):
        """Test valid Slack channel validation"""
        valid_channels = ["#general", "#dev-alerts", "#test_channel", "#TestChannel"]
        for channel in valid_channels:
            assert validate_slack_channel(channel) is True

    def test_validate_slack_channel_empty(self):
        """Test empty Slack channel raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack channel cannot be empty"):
            validate_slack_channel("")

    def test_validate_slack_channel_not_string(self):
        """Test non-string Slack channel raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack channel must be a string"):
            validate_slack_channel(123)

    def test_validate_slack_channel_no_hash(self):
        """Test Slack channel without # raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack channel must start with"):
            validate_slack_channel("general")

    def test_validate_slack_channel_empty_name(self):
        """Test Slack channel with only # raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack channel name cannot be empty"):
            validate_slack_channel("#")

    def test_validate_slack_channel_too_long(self):
        """Test overly long Slack channel raises ValidationError"""
        with pytest.raises(ValidationError, match="Slack channel name too long"):
            validate_slack_channel("#" + "a" * 81)

    def test_validate_slack_channel_invalid_chars(self):
        """Test Slack channel with invalid characters raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid Slack channel format"):
            validate_slack_channel("#test@channel")

    # Threshold Tests
    def test_validate_threshold_valid(self):
        """Test valid threshold validation"""
        valid_thresholds = [0, 50, 85.5, 100]
        for threshold in valid_thresholds:
            assert validate_threshold(threshold) is True

    def test_validate_threshold_none(self):
        """Test None threshold raises ValidationError"""
        with pytest.raises(ValidationError, match="Threshold cannot be None"):
            validate_threshold(None)

    def test_validate_threshold_not_number(self):
        """Test non-numeric threshold raises ValidationError"""
        with pytest.raises(ValidationError, match="Threshold must be a number"):
            validate_threshold("85")

    def test_validate_threshold_out_of_range(self):
        """Test out-of-range threshold raises ValidationError"""
        with pytest.raises(ValidationError, match="Threshold must be between"):
            validate_threshold(150)

    def test_validate_threshold_custom_range(self):
        """Test threshold with custom range"""
        assert validate_threshold(150, min_val=0, max_val=200) is True
        with pytest.raises(ValidationError, match="Threshold must be between"):
            validate_threshold(250, min_val=0, max_val=200)

    # URL Tests
    def test_validate_url_valid(self):
        """Test valid URL validation"""
        valid_urls = [
            "http://localhost:5001",
            "https://api.slack.com",
            "http://192.168.1.1:8080/health",
        ]
        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_empty(self):
        """Test empty URL raises ValidationError"""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_url("")

    def test_validate_url_not_string(self):
        """Test non-string URL raises ValidationError"""
        with pytest.raises(ValidationError, match="URL must be a string"):
            validate_url(123)

    def test_validate_url_wrong_scheme(self):
        """Test URL with wrong scheme raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid URL format"):
            validate_url("ftp://example.com")

    def test_validate_url_no_host(self):
        """Test URL without host raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid URL format"):
            validate_url("http://")

    # Hostname Tests
    def test_validate_hostname_valid(self):
        """Test valid hostname validation"""
        valid_hostnames = ["localhost", "example.com", "server-01", "192.168.1.1"]
        for hostname in valid_hostnames:
            assert validate_hostname(hostname) is True

    def test_validate_hostname_empty(self):
        """Test empty hostname raises ValidationError"""
        with pytest.raises(ValidationError, match="Hostname cannot be empty"):
            validate_hostname("")

    def test_validate_hostname_not_string(self):
        """Test non-string hostname raises ValidationError"""
        with pytest.raises(ValidationError, match="Hostname must be a string"):
            validate_hostname(123)

    def test_validate_hostname_too_long(self):
        """Test overly long hostname raises ValidationError"""
        with pytest.raises(ValidationError, match="Hostname too long"):
            validate_hostname("a" * 254)

    def test_validate_hostname_invalid_chars(self):
        """Test hostname with invalid characters raises ValidationError"""
        with pytest.raises(
            ValidationError, match="Hostname contains invalid characters"
        ):
            validate_hostname("host@name")

    def test_validate_hostname_consecutive_dots(self):
        """Test hostname with consecutive dots raises ValidationError"""
        with pytest.raises(
            ValidationError, match="Hostname cannot contain consecutive dots"
        ):
            validate_hostname("host..example.com")

    def test_validate_hostname_start_end_hyphen(self):
        """Test hostname starting with hyphen raises ValidationError"""
        with pytest.raises(
            ValidationError, match="Hostname cannot start or end with hyphen"
        ):
            validate_hostname("-hostname")

    def test_validate_hostname_empty_labels(self):
        """Test hostname with empty labels raises ValidationError"""
        # Test leading dot (creates empty first label)
        with pytest.raises(
            ValidationError, match="Hostname cannot contain empty labels"
        ):
            validate_hostname(".example.com")

    def test_validate_hostname_long_label(self):
        """Test hostname with long label raises ValidationError"""
        with pytest.raises(ValidationError, match="Hostname label too long"):
            validate_hostname("a" * 64 + ".com")

    def test_validate_hostname_label_hyphen(self):
        """Test hostname label with hyphen raises ValidationError"""
        with pytest.raises(
            ValidationError, match="Hostname label cannot start or end with hyphen"
        ):
            validate_hostname("host.-label.com")

    # Config Section Tests
    def test_validate_config_section_valid(self):
        """Test valid config section validation"""
        config = {
            "channel": "#test-alerts",
            "token": "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx",
        }
        assert (
            validate_config_section(
                config, "slack", required_fields=["channel"], optional_fields=["token"]
            )
            is True
        )

    def test_validate_config_section_not_dict(self):
        """Test non-dict config section raises ValidationError"""
        with pytest.raises(ValidationError, match="configuration must be a dictionary"):
            validate_config_section("not a dict", "test")

    def test_validate_config_section_missing_required(self):
        """Test missing required field raises ValidationError"""
        config = {"optional": "value"}
        with pytest.raises(ValidationError, match="Missing required field"):
            validate_config_section(config, "test", required_fields=["required_field"])

    def test_validate_config_section_invalid_slack_token(self):
        """Test invalid Slack token in config section raises ValidationError"""
        config = {"channel": "#test", "token": "invalid-token"}
        with pytest.raises(ValidationError, match="Invalid Slack token format"):
            validate_config_section(
                config, "slack", required_fields=["channel"], optional_fields=["token"]
            )

    def test_validate_config_section_invalid_threshold(self):
        """Test invalid threshold in config section raises ValidationError"""
        config = {
            "cpu_threshold": 150,
            "memory_threshold": 85,
            "disk_threshold": 90,
            "check_interval": 60,
        }
        with pytest.raises(ValidationError, match="Threshold must be between"):
            validate_config_section(
                config,
                "monitoring",
                required_fields=[
                    "cpu_threshold",
                    "memory_threshold",
                    "disk_threshold",
                    "check_interval",
                ],
            )

    def test_validate_config_section_invalid_check_interval(self):
        """Test invalid check interval raises ValidationError"""
        config = {
            "cpu_threshold": 90,
            "memory_threshold": 85,
            "disk_threshold": 90,
            "check_interval": -10,
        }
        with pytest.raises(
            ValidationError, match="Check interval must be a positive number"
        ):
            validate_config_section(
                config,
                "monitoring",
                required_fields=[
                    "cpu_threshold",
                    "memory_threshold",
                    "disk_threshold",
                    "check_interval",
                ],
            )

    # Complete Config Tests
    def test_validate_complete_config_valid(self):
        """Test valid complete config validation"""
        config = {
            "monitoring": {
                "cpu_threshold": 90,
                "memory_threshold": 85,
                "disk_threshold": 90,
                "check_interval": 60,
            },
            "slack": {"channel": "#test-alerts"},
            "remediator": {"url": "http://localhost:5001"},
        }
        assert validate_complete_config(config) is True

    def test_validate_complete_config_not_dict(self):
        """Test non-dict complete config raises ValidationError"""
        with pytest.raises(ValidationError, match="Configuration must be a dictionary"):
            validate_complete_config("not a dict")

    def test_validate_complete_config_invalid_section(self):
        """Test complete config with invalid section raises ValidationError"""
        config = {
            "monitoring": {
                "cpu_threshold": 150,  # Invalid
                "memory_threshold": 85,
                "disk_threshold": 90,
                "check_interval": 60,
            }
        }
        with pytest.raises(ValidationError, match="Threshold must be between"):
            validate_complete_config(config)
