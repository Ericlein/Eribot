import pytest
from config.models import MonitoringConfig, SlackConfig


@pytest.mark.unit
def test_monitoring_config_creation():
    """Test MonitoringConfig creation"""
    config = MonitoringConfig(
        cpu_threshold=90, disk_threshold=85, memory_threshold=80, check_interval=60
    )
    assert config.cpu_threshold == 90
    assert config.disk_threshold == 85


@pytest.mark.unit
def test_slack_config_creation():
    """Test SlackConfig creation"""
    config = SlackConfig(channel="#test", token="xoxb-test", username="TestBot")
    assert config.channel == "#test"
    assert config.token == "xoxb-test"
