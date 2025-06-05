"""
Tests for health_checker module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

from health_checker import (
    HealthStatus, 
    SystemHealthChecker, 
    ServiceHealthChecker, 
    CompositeHealthChecker
)


class TestHealthStatus:
    """Test HealthStatus data class"""

    def test_health_status_creation(self):
        """Test HealthStatus creation"""
        timestamp = datetime.now()
        details = {"test": "data"}
        
        status = HealthStatus(
            is_healthy=True,
            status="healthy",
            timestamp=timestamp,
            details=details,
            duration_ms=150.5
        )
        
        assert status.is_healthy is True
        assert status.status == "healthy"
        assert status.timestamp == timestamp
        assert status.details == details
        assert status.duration_ms == 150.5


class TestSystemHealthChecker:
    """Test SystemHealthChecker class"""

    @pytest.fixture
    def health_checker(self):
        """Create a SystemHealthChecker instance"""
        return SystemHealthChecker()

    @patch('health_checker.psutil.cpu_percent')
    @patch('health_checker.psutil.virtual_memory')
    @patch('health_checker.psutil.disk_usage')
    def test_check_system_health_all_healthy(self, mock_disk, mock_memory, mock_cpu, health_checker):
        """Test system health check when all components are healthy"""
        # Mock healthy system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=60.0, available=8000000000, total=16000000000)
        mock_disk.return_value = Mock(percent=70.0, free=300000000000, total=1000000000000)
        
        with patch('health_checker.socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect_ex.return_value = 0  # Successful connection
            
            result = health_checker.check_system_health()
            
            assert isinstance(result, HealthStatus)
            assert result.is_healthy is True
            assert "healthy" in result.status
            assert "cpu" in result.details
            assert "memory" in result.details
            assert "disk" in result.details
            assert "network" in result.details

    @patch('health_checker.psutil.cpu_percent')
    @patch('health_checker.psutil.virtual_memory')
    @patch('health_checker.psutil.disk_usage')
    def test_check_system_health_high_cpu(self, mock_disk, mock_memory, mock_cpu, health_checker):
        """Test system health check with high CPU usage"""
        # Mock high CPU usage
        mock_cpu.return_value = 95.0
        mock_memory.return_value = Mock(percent=60.0, available=8000000000, total=16000000000)
        mock_disk.return_value = Mock(percent=70.0, free=300000000000, total=1000000000000)
        
        with patch('health_checker.socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect_ex.return_value = 0
            
            result = health_checker.check_system_health()
            
            assert result.is_healthy is False
            assert "unhealthy" in result.status
            assert "CPU" in result.status

    @patch('health_checker.psutil.cpu_percent')
    @patch('health_checker.psutil.virtual_memory')
    @patch('health_checker.psutil.disk_usage')
    @patch('health_checker.socket.socket')
    def test_check_system_health_exception_handling(self, mock_socket, mock_disk, mock_memory, mock_cpu, health_checker):
        """Test system health check exception handling"""
        # Mock CPU to fail
        mock_cpu.side_effect = Exception("CPU monitoring failed")
        
        # Mock other components to work normally
        mock_memory.return_value = Mock(percent=60.0, available=8000000000, total=16000000000)
        mock_disk.return_value = Mock(percent=70.0, free=300000000000, total=1000000000000)
        
        # Mock network
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 0
        
        result = health_checker.check_system_health()
        
        # The actual behavior: CPU check fails but system continues
        assert result.is_healthy is False
        assert "unhealthy" in result.status
        assert "CPU: check failed" in result.status

    def test_check_cpu_healthy(self, health_checker):
        """Test CPU check when healthy"""
        with patch('health_checker.psutil.cpu_percent', return_value=45.0):
            with patch('health_checker.psutil.cpu_count', return_value=4):
                result = health_checker._check_cpu()
                
                assert result['healthy'] is True
                assert result['status'] == "normal"
                assert result['cpu_percent'] == 45.0
                assert result['cpu_count'] == 4

    def test_check_cpu_unhealthy(self, health_checker):
        """Test CPU check when unhealthy"""
        with patch('health_checker.psutil.cpu_percent', return_value=95.0):
            with patch('health_checker.psutil.cpu_count', return_value=4):
                result = health_checker._check_cpu()
                
                assert result['healthy'] is False
                assert "high usage" in result['status']
                assert result['cpu_percent'] == 95.0

    def test_check_memory_healthy(self, health_checker):
        """Test memory check when healthy"""
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.available = 8000000000
        mock_memory.total = 16000000000
        
        mock_swap = Mock()
        mock_swap.percent = 30.0
        
        with patch('health_checker.psutil.virtual_memory', return_value=mock_memory):
            with patch('health_checker.psutil.swap_memory', return_value=mock_swap):
                result = health_checker._check_memory()
                
                assert result['healthy'] is True
                assert result['status'] == "normal"
                assert result['percent'] == 60.0
                assert result['swap_percent'] == 30.0

    def test_check_disk_healthy(self, health_checker):
        """Test disk check when healthy"""
        mock_disk = Mock()
        mock_disk.percent = 70.0
        mock_disk.free = 300000000000  # 300GB
        mock_disk.total = 1000000000000  # 1TB
        
        with patch('health_checker.psutil.disk_usage', return_value=mock_disk):
            result = health_checker._check_disk()
            
            assert result['healthy'] is True
            assert result['status'] == "normal"
            assert result['percent'] == 70.0
            assert result['free_gb'] == 279.4  # Approximately 300GB


class TestServiceHealthChecker:
    """Test ServiceHealthChecker class"""

    @pytest.fixture
    def service_checker(self):
        """Create a ServiceHealthChecker instance"""
        return ServiceHealthChecker("http://localhost:5001")

    @patch('health_checker.requests.get')
    def test_check_remediator_service_healthy(self, mock_get, service_checker):
        """Test remediator service check when healthy"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response
        
        result = service_checker.check_remediator_service()
        
        assert result.is_healthy is True
        assert result.status == "service responding"
        assert result.details['status_code'] == 200

    @patch('health_checker.requests.get')
    def test_check_remediator_service_unhealthy(self, mock_get, service_checker):
        """Test remediator service check when unhealthy"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        result = service_checker.check_remediator_service()
        
        assert result.is_healthy is False
        assert "service returned status 503" in result.status
        assert result.details['status_code'] == 503

    @patch('health_checker.requests.get')
    def test_check_remediator_service_connection_error(self, mock_get, service_checker):
        """Test remediator service check with connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = service_checker.check_remediator_service()
        
        assert result.is_healthy is False
        assert result.status == "connection failed"
        assert result.details['error'] == 'connection_refused'

    @patch('health_checker.requests.get')
    def test_check_remediator_service_timeout(self, mock_get, service_checker):
        """Test remediator service check with timeout"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = service_checker.check_remediator_service(timeout=5.0)
        
        assert result.is_healthy is False
        assert "timeout after 5.0s" in result.status
        assert result.details['timeout_seconds'] == 5.0

    def test_check_slack_connectivity_success(self, service_checker):
        """Test successful Slack connectivity check"""
        # Mock the slack_sdk module since it's imported inside the method
        mock_webclient = Mock()
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.auth_test.return_value = {
            'user': 'test_bot',
            'team': 'test_team'
        }
        
        # Mock the entire slack_sdk module
        mock_slack_sdk = Mock()
        mock_slack_sdk.WebClient = mock_webclient
        
        with patch.dict('sys.modules', {'slack_sdk': mock_slack_sdk}):
            result = service_checker.check_slack_connectivity("xoxb-test-token")
            
            assert result.is_healthy is True
            assert result.status == "slack api accessible"
            assert result.details['user'] == 'test_bot'
            assert result.details['team'] == 'test_team'

    def test_check_slack_connectivity_api_error(self, service_checker):
        """Test Slack connectivity check with API error"""
        # Create a mock SlackApiError class
        class MockSlackApiError(Exception):
            def __init__(self, message, response):
                super().__init__(message)
                self.response = response
        
        # Mock the slack_sdk module
        mock_webclient = Mock()
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        
        # Make auth_test raise the mock error
        mock_client.auth_test.side_effect = MockSlackApiError(
            "Invalid token", 
            {"error": "invalid_auth"}
        )
        
        # Create mock slack_sdk module with proper structure
        mock_slack_sdk = Mock()
        mock_slack_sdk.WebClient = mock_webclient
        mock_slack_sdk.errors = Mock()
        mock_slack_sdk.errors.SlackApiError = MockSlackApiError
        
        with patch.dict('sys.modules', {
            'slack_sdk': mock_slack_sdk,
            'slack_sdk.errors': mock_slack_sdk.errors
        }):
            result = service_checker.check_slack_connectivity("xoxb-invalid-token")
            
            assert result.is_healthy is False
            assert "slack api error: invalid_auth" in result.status
            assert result.details['error'] == 'invalid_auth'


class TestCompositeHealthChecker:
    """Test CompositeHealthChecker class"""

    @pytest.fixture
    def composite_checker(self):
        """Create a CompositeHealthChecker instance"""
        return CompositeHealthChecker("http://localhost:5001", "xoxb-test-token")

    @patch.object(SystemHealthChecker, 'check_system_health')
    @patch.object(ServiceHealthChecker, 'check_remediator_service')
    @patch.object(ServiceHealthChecker, 'check_slack_connectivity')
    def test_check_all_health(self, mock_slack_check, mock_remediator_check, mock_system_check, composite_checker):
        """Test checking all health components"""
        # Mock health statuses
        mock_system_check.return_value = HealthStatus(
            is_healthy=True,
            status="healthy",
            timestamp=datetime.now(),
            details={},
            duration_ms=100
        )
        mock_remediator_check.return_value = HealthStatus(
            is_healthy=True,
            status="service responding",
            timestamp=datetime.now(),
            details={},
            duration_ms=50
        )
        mock_slack_check.return_value = HealthStatus(
            is_healthy=True,
            status="slack api accessible",
            timestamp=datetime.now(),
            details={},
            duration_ms=75
        )
        
        results = composite_checker.check_all_health()
        
        assert 'system' in results
        assert 'remediator' in results
        assert 'slack' in results
        assert all(status.is_healthy for status in results.values())

    @patch.object(SystemHealthChecker, 'check_system_health')
    @patch.object(ServiceHealthChecker, 'check_remediator_service')
    @patch.object(ServiceHealthChecker, 'check_slack_connectivity')
    def test_get_overall_health_all_healthy(self, mock_slack_check, mock_remediator_check, mock_system_check, composite_checker):
        """Test overall health when all components are healthy"""
        # Mock all components as healthy
        mock_system_check.return_value = HealthStatus(
            is_healthy=True,
            status="healthy",
            timestamp=datetime.now(),
            details={},
            duration_ms=100
        )
        mock_remediator_check.return_value = HealthStatus(
            is_healthy=True,
            status="service responding",
            timestamp=datetime.now(),
            details={},
            duration_ms=50
        )
        mock_slack_check.return_value = HealthStatus(
            is_healthy=True,
            status="slack api accessible",
            timestamp=datetime.now(),
            details={},
            duration_ms=75
        )
        
        result = composite_checker.get_overall_health()
        
        assert result.is_healthy is True
        assert result.status == "all components healthy"
        assert 'components' in result.details

    @patch.object(SystemHealthChecker, 'check_system_health')
    @patch.object(ServiceHealthChecker, 'check_remediator_service')
    def test_get_overall_health_with_unhealthy_component(self, mock_remediator_check, mock_system_check):
        """Test overall health when some components are unhealthy"""
        # Create checker without Slack token to avoid checking Slack
        composite_checker = CompositeHealthChecker("http://localhost:5001", "")
        
        # Mock system as healthy, remediator as unhealthy
        mock_system_check.return_value = HealthStatus(
            is_healthy=True,
            status="healthy",
            timestamp=datetime.now(),
            details={},
            duration_ms=100
        )
        mock_remediator_check.return_value = HealthStatus(
            is_healthy=False,
            status="connection failed",
            timestamp=datetime.now(),
            details={},
            duration_ms=50
        )
        
        result = composite_checker.get_overall_health()
        
        assert result.is_healthy is False
        assert "unhealthy components: remediator" in result.status
        assert 'components' in result.details