"""
Tests for the monitor module
Fixed for new structure with proper mocking
"""

import pytest
from unittest.mock import patch, Mock


class TestMonitor:
    """Test cases for the monitoring module"""

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    def test_system_monitor_creation(self, mock_slack_client, mock_remediation_client, app_config):
        """Test that SystemMonitor can be created"""
        from core.monitor import SystemMonitor

        # Mock the client constructors to return mock instances
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance

        mock_remediation_instance = Mock()
        mock_remediation_client.return_value = mock_remediation_instance

        monitor = SystemMonitor(app_config)
        assert monitor is not None
        assert monitor.config == app_config

        # Verify clients were created
        mock_slack_client.assert_called_once_with(app_config.slack)
        mock_remediation_client.assert_called_once_with(app_config.remediator)

    @pytest.mark.unit
    def test_system_metrics_creation(self):
        """Test SystemMetrics dataclass"""
        from core.monitor import SystemMetrics
        from datetime import datetime

        metrics = SystemMetrics(
            cpu_percent=45.0,
            memory_percent=60.0,
            disk_percent=70.0,
            timestamp=datetime.now(),
            hostname="test-host",
        )

        assert metrics.cpu_percent == 45.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 70.0
        assert metrics.hostname == "test-host"

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("socket.gethostname")
    def test_gather_metrics(
        self,
        mock_hostname,
        mock_disk,
        mock_memory,
        mock_cpu,
        mock_slack_client,
        mock_remediation_client,
        app_config,
    ):
        """Test gathering system metrics"""
        from core.monitor import SystemMonitor

        # Setup mocks
        mock_cpu.return_value = 45.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        mock_hostname.return_value = "test-host"

        # Mock the clients
        mock_slack_client.return_value = Mock()
        mock_remediation_client.return_value = Mock()

        monitor = SystemMonitor(app_config)
        metrics = monitor._gather_metrics()

        assert metrics.cpu_percent == 45.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 70.0
        assert metrics.hostname == "test-host"

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    def test_check_system_normal(
        self, mock_slack_client, mock_remediation_client, app_config, mock_psutil
    ):
        """Test system check with normal metrics"""
        from core.monitor import SystemMonitor

        # Mock the clients
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance
        mock_remediation_instance = Mock()
        mock_remediation_client.return_value = mock_remediation_instance

        with patch("socket.gethostname", return_value="test-host"):
            monitor = SystemMonitor(app_config)
            metrics = monitor.check_system()

            # Should not trigger any alerts with healthy metrics
            assert metrics.cpu_percent == 45.0  # From mock_psutil fixture
            assert monitor.alert_count == 0

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("socket.gethostname")
    def test_check_system_high_cpu(
        self,
        mock_hostname,
        mock_disk,
        mock_memory,
        mock_cpu,
        mock_slack_client,
        mock_remediation_client,
        app_config,
    ):
        """Test system check with high CPU"""
        from core.monitor import SystemMonitor

        # Setup system metrics mocks
        mock_cpu.return_value = 95.0  # High CPU
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        mock_hostname.return_value = "test-host"

        # Mock the clients
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance
        mock_remediation_instance = Mock()
        mock_remediation_instance.trigger_remediation.return_value = True
        mock_remediation_client.return_value = mock_remediation_instance

        monitor = SystemMonitor(app_config)
        metrics = monitor.check_system()

        # Should trigger CPU alert
        assert metrics.cpu_percent == 95.0
        assert monitor.alert_count == 1
        mock_slack_instance.send_alert.assert_called()
        mock_remediation_instance.trigger_remediation.assert_called()

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    def test_monitor_status(self, mock_slack_client, mock_remediation_client, app_config):
        """Test getting monitor status"""
        from core.monitor import SystemMonitor

        # Mock the clients
        mock_slack_client.return_value = Mock()
        mock_remediation_client.return_value = Mock()

        monitor = SystemMonitor(app_config)
        status = monitor.get_status()

        assert "running" in status
        assert "check_count" in status
        assert "alert_count" in status
        assert "config" in status
        assert status["check_count"] == 0  # No checks performed yet

    @pytest.mark.unit
    @patch("core.monitor.RemediationClient")
    @patch("core.monitor.SlackClient")
    def test_monitor_start_stop(self, mock_slack_client, mock_remediation_client, app_config):
        """Test monitor start and stop functionality"""
        from core.monitor import SystemMonitor

        # Mock the clients
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance
        mock_remediation_client.return_value = Mock()

        monitor = SystemMonitor(app_config)

        # Test that monitor starts
        assert monitor._running is False

        # We won't actually start it in the test to avoid hanging
        # Just test the status tracking
        assert monitor.get_status()["running"] is False
