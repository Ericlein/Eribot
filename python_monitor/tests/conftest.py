"""
Pytest configuration and shared fixtures for EriBot tests
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import Mock, patch
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import SlackConfig, MonitoringConfig, RemediatorConfig, AppConfig
from health_checker import HealthStatus


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'SLACK_BOT_TOKEN': 'xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx',
        'SLACK_CHANNEL': '#test-alerts',
        'CPU_THRESHOLD': '90',
        'DISK_THRESHOLD': '90',
        'CHECK_INTERVAL': '60',
        'REMEDIATOR_URL': 'http://localhost:5001',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def test_config():
    """Create a test configuration dictionary"""
    return {
        'monitoring': {
            'cpu_threshold': 90,
            'disk_threshold': 90,
            'memory_threshold': 90,
            'check_interval': 60
        },
        'slack': {
            'channel': '#test-alerts'
        },
        'remediator': {
            'url': 'http://localhost:5001',
            'timeout': 30
        }
    }


@pytest.fixture
def temp_config_file(test_config):
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def slack_config():
    """Create a test Slack configuration"""
    return SlackConfig(
        channel='#test-alerts',
        token='xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx'
    )


@pytest.fixture
def monitoring_config():
    """Create a test monitoring configuration"""
    return MonitoringConfig(
        cpu_threshold=90,
        disk_threshold=90,
        check_interval=60
    )


@pytest.fixture
def remediator_config():
    """Create a test remediator configuration"""
    return RemediatorConfig(url='http://localhost:5001')


@pytest.fixture
def app_config(monitoring_config, slack_config, remediator_config):
    """Create a complete test application configuration"""
    return AppConfig(
        monitoring=monitoring_config,
        slack=slack_config,
        remediator=remediator_config
    )


@pytest.fixture
def healthy_system_metrics():
    """Mock healthy system metrics"""
    return {
        'timestamp': datetime.now().isoformat(),
        'hostname': 'test-server',
        'platform': 'Linux',
        'cpu': {
            'percent': 45.0,
            'count': 4,
            'load_avg': [0.5, 0.6, 0.7]
        },
        'memory': {
            'percent': 60.0,
            'available_gb': 8.0,
            'total_gb': 16.0
        },
        'disk': {
            'percent': 70.0,
            'free_gb': 100.0,
            'total_gb': 500.0
        }
    }


@pytest.fixture
def unhealthy_system_metrics():
    """Mock unhealthy system metrics"""
    return {
        'timestamp': datetime.now().isoformat(),
        'hostname': 'test-server',
        'platform': 'Linux',
        'cpu': {
            'percent': 95.0,  # High CPU
            'count': 4,
            'load_avg': [3.0, 3.5, 4.0]
        },
        'memory': {
            'percent': 95.0,  # High memory
            'available_gb': 0.5,
            'total_gb': 16.0
        },
        'disk': {
            'percent': 95.0,  # High disk
            'free_gb': 5.0,
            'total_gb': 500.0
        }
    }


@pytest.fixture
def mock_psutil():
    """Mock psutil module with healthy defaults"""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.cpu_count') as mock_cpu_count, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.swap_memory') as mock_swap, \
         patch('psutil.disk_usage') as mock_disk:
        
        # Healthy defaults
        mock_cpu.return_value = 45.0
        mock_cpu_count.return_value = 4
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 8 * 1024**3  # 8GB
        mock_memory_obj.total = 16 * 1024**3  # 16GB
        mock_memory.return_value = mock_memory_obj
        
        mock_swap_obj = Mock()
        mock_swap_obj.percent = 30.0
        mock_swap.return_value = mock_swap_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 70.0
        mock_disk_obj.free = 100 * 1024**3  # 100GB
        mock_disk_obj.total = 500 * 1024**3  # 500GB
        mock_disk.return_value = mock_disk_obj
        
        yield {
            'cpu': mock_cpu,
            'cpu_count': mock_cpu_count,
            'memory': mock_memory,
            'swap': mock_swap,
            'disk': mock_disk
        }


@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient"""
    with patch('slack_client.WebClient') as mock_webclient:
        mock_instance = Mock()
        mock_webclient.return_value = mock_instance
        
        # Mock successful auth_test
        mock_instance.auth_test.return_value = {
            'ok': True,
            'user': 'test_bot',
            'team': 'test_team'
        }
        
        # Mock successful message posting
        mock_instance.chat_postMessage.return_value = {
            'ok': True,
            'channel': '#test-alerts',
            'ts': '1234567890.123456'
        }
        
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock requests module for HTTP calls"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'healthy'}
        mock_response.text = 'OK'
        mock_response.raise_for_status.return_value = None
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }


@pytest.fixture
def healthy_health_status():
    """Create a healthy HealthStatus object"""
    return HealthStatus(
        is_healthy=True,
        status="healthy",
        timestamp=datetime.now(),
        details={'test': 'data'},
        duration_ms=50.0
    )


@pytest.fixture
def unhealthy_health_status():
    """Create an unhealthy HealthStatus object"""
    return HealthStatus(
        is_healthy=False,
        status="unhealthy: high CPU usage",
        timestamp=datetime.now(),
        details={'cpu_percent': 95.0, 'error': 'threshold exceeded'},
        duration_ms=75.0
    )


@pytest.fixture
def mock_file_operations():
    """Mock file system operations"""
    with patch('builtins.open') as mock_open_func, \
         patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        mock_exists.return_value = True
        mock_makedirs.return_value = None
        
        # Mock temporary file
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test_file'
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        yield {
            'open': mock_open_func,
            'exists': mock_exists,
            'makedirs': mock_makedirs,
            'temp': mock_temp
        }


@pytest.fixture
def mock_socket():
    """Mock socket operations for network tests"""
    with patch('socket.socket') as mock_socket_class:
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance
        
        # Mock successful connection
        mock_socket_instance.connect_ex.return_value = 0
        mock_socket_instance.close.return_value = None
        
        yield mock_socket_instance


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment before and after each test"""
    # Store original environment
    original_env = dict(os.environ)
    
    yield
    
    # Restore environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs(caplog):
    """Capture logs with specific level"""
    import logging
    with caplog.at_level(logging.DEBUG):
        yield caplog


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


# Test utilities
class TestHelpers:
    """Helper functions for tests"""
    
    @staticmethod
    def create_mock_response(status_code=200, json_data=None, text="OK"):
        """Create a mock HTTP response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        mock_response.text = text
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    @staticmethod
    def assert_health_status(health_status, expected_healthy=True, expected_status=None):
        """Assert health status properties"""
        assert isinstance(health_status, HealthStatus)
        assert health_status.is_healthy == expected_healthy
        if expected_status:
            assert expected_status in health_status.status
        assert health_status.duration_ms >= 0
        assert isinstance(health_status.details, dict)
    
    @staticmethod
    def assert_config_valid(config, config_type):
        """Assert configuration is valid"""
        assert isinstance(config, config_type)
        # Add specific assertions based on config type
        if hasattr(config, 'cpu_threshold'):
            assert 0 <= config.cpu_threshold <= 100
        if hasattr(config, 'channel'):
            assert config.channel.startswith('#')


@pytest.fixture
def test_helpers():
    """Provide test helper functions"""
    return TestHelpers


# Custom assertions
def assert_no_errors(caplog):
    """Assert no error logs were captured"""
    errors = [record for record in caplog.records if record.levelno >= 40]  # ERROR and CRITICAL
    assert len(errors) == 0, f"Unexpected errors: {[r.message for r in errors]}"


def assert_contains_log(caplog, message, level="INFO"):
    """Assert that logs contain a specific message"""
    import logging
    level_num = getattr(logging, level.upper())
    matching_records = [
        record for record in caplog.records 
        if record.levelno == level_num and message in record.message
    ]
    assert len(matching_records) > 0, f"Expected log message '{message}' not found"


# Add custom assertions to pytest namespace
pytest.assert_no_errors = assert_no_errors
pytest.assert_contains_log = assert_contains_log