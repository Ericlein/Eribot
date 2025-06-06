"""
Tests for configuration models
"""

import pytest

from config.models import (
    MonitoringConfig,
    SlackConfig, 
    RemediatorConfig,
    LoggingConfig,
    AppConfig
)


class TestConfigModels:
    """Test configuration data models"""
    
    @pytest.mark.unit
    def test_monitoring_config_creation(self):
        """Test MonitoringConfig creation"""
        config = MonitoringConfig(
            cpu_threshold=90,
            disk_threshold=85,
            memory_threshold=80,
            check_interval=60
        )
        assert config.cpu_threshold == 90
        assert config.disk_threshold == 85
        assert config.memory_threshold == 80
        assert config.check_interval == 60
    
    @pytest.mark.unit
    def test_slack_config_creation(self):
        """Test SlackConfig creation"""
        config = SlackConfig(
            channel="#test",
            token="xoxb-test-token",
            username="TestBot",
            icon_emoji=":robot:"
        )
        assert config.channel == "#test"
        assert config.token == "xoxb-test-token"
        assert config.username == "TestBot"
        assert config.icon_emoji == ":robot:"
    
    @pytest.mark.unit
    def test_slack_config_defaults(self):
        """Test SlackConfig with defaults"""
        config = SlackConfig(
            channel="#test",
            token="xoxb-test-token"
        )
        assert config.channel == "#test"
        assert config.token == "xoxb-test-token"
        assert config.username == "EriBot"
        assert config.icon_emoji == ":robot_face:"
    
    @pytest.mark.unit
    def test_remediator_config_creation(self):
        """Test RemediatorConfig creation"""
        config = RemediatorConfig(
            url="http://localhost:5001",
            timeout=30,
            retry_attempts=3
        )
        assert config.url == "http://localhost:5001"
        assert config.timeout == 30
        assert config.retry_attempts == 3
    
    @pytest.mark.unit
    def test_remediator_config_defaults(self):
        """Test RemediatorConfig with defaults"""
        config = RemediatorConfig(
            url="http://localhost:5001"
        )
        assert config.url == "http://localhost:5001"
        assert config.timeout == 30
        assert config.retry_attempts == 3
    
    @pytest.mark.unit
    def test_logging_config_creation(self):
        """Test LoggingConfig creation"""
        config = LoggingConfig(
            level="DEBUG",
            max_file_size="20MB",
            backup_count=10,
            console_output=False
        )
        assert config.level == "DEBUG"
        assert config.max_file_size == "20MB"
        assert config.backup_count == 10
        assert config.console_output is False
    
    @pytest.mark.unit
    def test_logging_config_defaults(self):
        """Test LoggingConfig with defaults"""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.max_file_size == "10MB"
        assert config.backup_count == 5
        assert config.console_output is True
    
    @pytest.mark.unit
    def test_app_config_creation(self):
        """Test AppConfig creation"""
        monitoring = MonitoringConfig(90, 85, 80, 60)
        slack = SlackConfig("#test", "xoxb-test")
        remediator = RemediatorConfig("http://localhost:5001")
        logging = LoggingConfig()
        
        config = AppConfig(
            monitoring=monitoring,
            slack=slack,
            remediator=remediator,
            logging=logging
        )
        
        assert config.monitoring == monitoring
        assert config.slack == slack
        assert config.remediator == remediator
        assert config.logging == logging