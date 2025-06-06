"""
Centralized pytest configuration and fixtures for EriBot tests
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import Mock, patch
from datetime import datetime
from config.models import (
    SlackConfig,
    MonitoringConfig,
    RemediatorConfig,
    AppConfig,
    LoggingConfig,
)
from core.health import HealthStatus


# ---------------------
# Pytest CLI options
# ---------------------
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires real API credentials)",
    )


# ---------------------
# Environment handling
# ---------------------
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        "SLACK_BOT_TOKEN": "xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx",
        "SLACK_CHANNEL": "#test-alerts",
        "CPU_THRESHOLD": "90",
        "DISK_THRESHOLD": "90",
        "CHECK_INTERVAL": "60",
        "REMEDIATOR_URL": "http://localhost:5001",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment before and after each test"""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def skip_integration_in_ci(request):
    """Automatically skip integration tests in CI environment"""
    if request.node.get_closest_marker("integration"):
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            pytest.skip("Integration tests skipped in CI environment")


# ---------------------
# Config fixtures
# ---------------------
@pytest.fixture
def test_config():
    """Create a test configuration dictionary"""
    return {
        "monitoring": {
            "cpu_threshold": 90,
            "disk_threshold": 90,
            "memory_threshold": 90,
            "check_interval": 60,
        },
        "slack": {"channel": "#test-alerts"},
        "remediator": {"url": "http://localhost:5001", "timeout": 30},
    }


@pytest.fixture
def temp_config_file(test_config):
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_config, f)
        temp_file = f.name
    yield temp_file
    os.unlink(temp_file)


@pytest.fixture
def slack_config():
    """Provide Slack configuration for tests"""
    return SlackConfig(
        channel="#test-alerts",
        token="xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx",
    )


@pytest.fixture
def monitoring_config():
    """Create a test monitoring configuration"""
    return MonitoringConfig(
        cpu_threshold=90, disk_threshold=90, memory_threshold=90, check_interval=60
    )


@pytest.fixture
def remediator_config():
    """Create a test remediator configuration"""
    return RemediatorConfig(url="http://localhost:5001")


@pytest.fixture
def app_config(monitoring_config, slack_config, remediator_config):
    """Create a complete test application configuration"""
    return AppConfig(
        monitoring=monitoring_config,
        slack=slack_config,
        remediator=remediator_config,
        logging=LoggingConfig(),
    )


# ---------------------
# Mocked system metrics
# ---------------------
@pytest.fixture
def healthy_system_metrics():
    """Mock healthy system metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "hostname": "test-server",
        "platform": "Linux",
        "cpu": {"percent": 45.0, "count": 4, "load_avg": [0.5, 0.6, 0.7]},
        "memory": {"percent": 60.0, "available_gb": 8.0, "total_gb": 16.0},
        "disk": {"percent": 70.0, "free_gb": 100.0, "total_gb": 500.0},
    }


@pytest.fixture
def mock_psutil():
    """Mock psutil module with healthy defaults"""
    with patch("psutil.cpu_percent") as mock_cpu, patch(
        "psutil.cpu_count"
    ) as mock_cpu_count, patch("psutil.virtual_memory") as mock_memory, patch(
        "psutil.swap_memory"
    ) as mock_swap, patch(
        "psutil.disk_usage"
    ) as mock_disk:

        mock_cpu.return_value = 45.0
        mock_cpu_count.return_value = 4

        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 8 * 1024**3
        mock_memory_obj.total = 16 * 1024**3
        mock_memory.return_value = mock_memory_obj

        mock_swap_obj = Mock()
        mock_swap_obj.percent = 30.0
        mock_swap.return_value = mock_swap_obj

        mock_disk_obj = Mock()
        mock_disk_obj.percent = 70.0
        mock_disk_obj.free = 100 * 1024**3
        mock_disk_obj.total = 500 * 1024**3
        mock_disk.return_value = mock_disk_obj

        yield {
            "cpu": mock_cpu,
            "cpu_count": mock_cpu_count,
            "memory": mock_memory,
            "swap": mock_swap,
            "disk": mock_disk,
        }


# ---------------------
# Mock Slack client
# ---------------------
@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient"""
    with patch("clients.slack.WebClient") as mock_webclient:
        mock_instance = Mock()
        mock_webclient.return_value = mock_instance

        mock_instance.auth_test.return_value = {
            "ok": True,
            "user": "test_bot",
            "team": "test_team",
        }

        mock_instance.chat_postMessage.return_value = {
            "ok": True,
            "channel": "#test-alerts",
            "ts": "1234567890.123456",
        }

        yield mock_instance


# ---------------------
# Health Status mock
# ---------------------
@pytest.fixture
def healthy_health_status():
    """Create a healthy HealthStatus object"""
    return HealthStatus(
        is_healthy=True,
        status="healthy",
        timestamp=datetime.now(),
        details={"test": "data"},
        duration_ms=50.0,
    )


# ---------------------
# Pytest markers
# ---------------------
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "network: mark test as requiring network access")


# ---------------------
# Custom assertions
# ---------------------
def assert_no_errors(caplog):
    """Assert no error logs were captured"""
    errors = [record for record in caplog.records if record.levelno >= 40]
    assert len(errors) == 0, f"Unexpected errors: {[r.message for r in errors]}"


def assert_contains_log(caplog, message, level="INFO"):
    """Assert that logs contain a specific message"""
    import logging

    level_num = getattr(logging, level.upper())
    matching_records = [
        record
        for record in caplog.records
        if record.levelno == level_num and message in record.message
    ]
    assert len(matching_records) > 0, f"Expected log message '{message}' not found"


pytest.assert_no_errors = assert_no_errors
pytest.assert_contains_log = assert_contains_log
