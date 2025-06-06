import pytest
import requests
import time
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require external services"""

    @pytest.mark.integration
    def test_remediator_service_connection(self):
        """Test connection to C# remediator service"""
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            assert response.status_code in [
                200,
                404,
            ]  # 404 is OK if health endpoint doesn't exist
        except requests.exceptions.ConnectionError:
            pytest.skip("C# remediator service not running")

    @pytest.mark.integration
    @patch("core.monitor.SlackClient")
    @patch("core.monitor.RemediationClient")
    def test_end_to_end_monitoring(self, mock_remediation_client, mock_slack_client, app_config):
        """Test complete monitoring flow"""
        from core.monitor import SystemMonitor

        # Mock the client classes to return mock instances
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance

        mock_remediation_instance = Mock()
        mock_remediation_client.return_value = mock_remediation_instance

        # Create monitor instance
        monitor = SystemMonitor(app_config)

        # Run system check
        metrics = monitor.check_system()

        # Verify we got valid SystemMetrics
        assert hasattr(metrics, "cpu_percent")
        assert hasattr(metrics, "memory_percent")
        assert hasattr(metrics, "disk_percent")
        assert hasattr(metrics, "timestamp")
        assert hasattr(metrics, "hostname")

        # Check metric ranges
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert 0 <= metrics.disk_percent <= 100
        assert metrics.hostname is not None

    @pytest.mark.integration
    @patch("core.monitor.SlackClient")
    @patch("core.monitor.RemediationClient")
    def test_monitoring_with_high_thresholds(
        self, mock_remediation_client, mock_slack_client, app_config
    ):
        """Test monitoring with artificially high resource usage"""
        from core.monitor import SystemMonitor

        # Mock the client classes to return mock instances
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance

        mock_remediation_instance = Mock()
        mock_remediation_instance.trigger_remediation.return_value = True
        mock_remediation_client.return_value = mock_remediation_instance

        # Create monitor with lower thresholds to trigger alerts
        app_config.monitoring.cpu_threshold = 1.0  # Very low to trigger alert
        app_config.monitoring.memory_threshold = 1.0
        app_config.monitoring.disk_threshold = 1.0

        monitor = SystemMonitor(app_config)

        # Run check - should trigger alerts due to low thresholds
        metrics = monitor.check_system()

        # Verify metrics are still valid
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert 0 <= metrics.disk_percent <= 100

        # Should have triggered alerts due to low thresholds
        assert monitor.alert_count > 0

    @pytest.mark.integration
    @pytest.mark.slow
    @patch("core.monitor.SlackClient")
    @patch("core.monitor.RemediationClient")
    def test_monitoring_loop(self, mock_remediation_client, mock_slack_client, app_config):
        """Test monitoring loop for a short duration"""
        from core.monitor import SystemMonitor

        # Mock the client classes to return mock instances
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance

        mock_remediation_instance = Mock()
        mock_remediation_client.return_value = mock_remediation_instance

        monitor = SystemMonitor(app_config)

        # Run monitoring for 3 iterations
        results = []
        for _ in range(3):
            metrics = monitor.check_system()
            results.append(metrics)
            time.sleep(1)

        # Verify we got 3 results
        assert len(results) == 3

        # Verify all results are valid SystemMetrics objects
        for metrics in results:
            assert hasattr(metrics, "cpu_percent")
            assert hasattr(metrics, "memory_percent")
            assert hasattr(metrics, "disk_percent")
            assert 0 <= metrics.cpu_percent <= 100
            assert 0 <= metrics.memory_percent <= 100
            assert 0 <= metrics.disk_percent <= 100

        # Verify monitor tracked the checks
        assert monitor.check_count == 3

    @pytest.mark.integration
    def test_health_checker_integration(self):
        """Test health checker functionality"""
        from core.health import SystemHealthChecker, ServiceHealthChecker

        # Test system health checker
        system_checker = SystemHealthChecker()
        health_status = system_checker.check_system_health()

        assert hasattr(health_status, "is_healthy")
        assert hasattr(health_status, "status")
        assert hasattr(health_status, "timestamp")
        assert hasattr(health_status, "details")
        assert isinstance(health_status.details, dict)

        # Test service health checker (will fail if service not running, which is expected)
        service_checker = ServiceHealthChecker("http://localhost:5001")
        service_status = service_checker.check_remediator_service()

        assert hasattr(service_status, "is_healthy")
        assert hasattr(service_status, "status")
        # Service might be down in tests, so we don't assert is_healthy is True

    @pytest.mark.integration
    @patch("core.monitor.SlackClient")
    @patch("core.monitor.RemediationClient")
    def test_config_integration(self, mock_remediation_client, mock_slack_client, app_config):
        """Test that configuration integrates properly with monitor"""
        from core.monitor import SystemMonitor

        # Mock the client classes to return mock instances
        mock_slack_instance = Mock()
        mock_slack_client.return_value = mock_slack_instance

        mock_remediation_instance = Mock()
        mock_remediation_client.return_value = mock_remediation_instance

        # Verify monitor can be created with config
        monitor = SystemMonitor(app_config)

        # Verify config is accessible
        assert monitor.config.monitoring.cpu_threshold == app_config.monitoring.cpu_threshold
        assert monitor.config.slack.channel == app_config.slack.channel
        assert monitor.config.remediator.url == app_config.remediator.url

        # Verify status includes config
        status = monitor.get_status()
        assert "config" in status
        assert "running" in status
        assert "check_count" in status
