"""
Tests for health_checker module
Fixed for new structure
"""

import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

# Import from new structure
from core.health import (
    HealthStatus,
    SystemHealthChecker,
    ServiceHealthChecker,
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
            duration_ms=150.5,
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

    @pytest.mark.unit
    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    def test_check_system_health_all_healthy(
        self, mock_disk, mock_memory, mock_cpu, health_checker
    ):
        """Test system health check when all components are healthy"""
        # Mock healthy system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(
            percent=60.0, available=8000000000, total=16000000000
        )
        mock_disk.return_value = Mock(
            percent=70.0, free=300000000000, total=1000000000000
        )

        with patch("socket.socket") as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect_ex.return_value = 0  # Successful connection

            result = health_checker.check_system_health()

            assert isinstance(result, HealthStatus)
            assert result.is_healthy is True
            assert "healthy" in result.status


class TestServiceHealthChecker:
    """Test ServiceHealthChecker class"""

    @pytest.fixture
    def service_checker(self):
        """Create a ServiceHealthChecker instance"""
        return ServiceHealthChecker("http://localhost:5001")

    @pytest.mark.unit
    @patch("requests.get")
    def test_check_remediator_service_healthy(self, mock_get, service_checker):
        """Test remediator service check when healthy"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        result = service_checker.check_remediator_service()

        assert result.is_healthy is True
        assert result.status == "service responding"

    @pytest.mark.unit
    @patch("requests.get")
    def test_check_remediator_service_connection_error(self, mock_get, service_checker):
        """Test remediator service check with connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = service_checker.check_remediator_service()

        assert result.is_healthy is False
        assert result.status == "connection failed"
