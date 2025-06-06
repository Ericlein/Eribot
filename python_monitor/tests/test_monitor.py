"""
Tests for the monitor module
"""

import pytest
from unittest.mock import patch, MagicMock, Mock, call
import sys
import os
import builtins

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMonitor:
    """Test cases for the monitoring module"""
    
    @pytest.fixture(autouse=True)
    def setup_module_mocks(self):
        """Setup mocks for module-level imports"""
        # We need to mock these before importing the module
        with patch('monitor.load_dotenv'):
            with patch('monitor.ConfigLoader') as mock_config_loader:
                # Setup config mock
                mock_config = Mock()
                mock_config.monitoring.cpu_threshold = 90  # Changed to match actual config
                mock_config.monitoring.disk_threshold = 90
                mock_config.monitoring.memory_threshold = 90
                mock_config.monitoring.check_interval = 60
                mock_config.remediator = Mock()
                
                mock_loader_instance = Mock()
                mock_loader_instance.load.return_value = mock_config
                mock_loader_instance.validate.return_value = True
                mock_config_loader.return_value = mock_loader_instance
                
                with patch('monitor.RemediationClient'):
                    # Now we can safely import
                    import monitor
                    self.monitor = monitor
                    yield
    
    @pytest.mark.unit
    @patch('monitor.psutil.cpu_percent')
    @patch('monitor.psutil.disk_usage')
    @patch('monitor.psutil.virtual_memory')
    @patch('monitor.send_slack_message')
    @patch('monitor.trigger_remediation')
    def test_check_system_normal(self, mock_trigger, mock_slack, mock_memory, mock_disk, mock_cpu):
        """Test system check with normal CPU and disk usage"""
        mock_cpu.return_value = 50.0
        mock_disk.return_value = MagicMock(percent=60.0)
        mock_memory.return_value = MagicMock(percent=40.0)
        
        cpu, disk = self.monitor.check_system()
        
        assert cpu == 50.0
        assert disk == 60.0
        mock_slack.assert_not_called()
        mock_trigger.assert_not_called()
    
    @pytest.mark.unit
    def test_check_system_high_cpu(self):
        """Test system check with high CPU usage"""
        with patch('monitor.psutil.cpu_percent', return_value=95.0):  # Above 90% threshold
            with patch('monitor.psutil.disk_usage') as mock_disk:
                mock_disk.return_value = MagicMock(percent=60.0)
                with patch('monitor.psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value = MagicMock(percent=40.0)
                    with patch('monitor.send_slack_message') as mock_slack:
                        with patch.object(self.monitor, 'trigger_remediation') as mock_trigger:
                            cpu, disk = self.monitor.check_system()
                            
                            assert cpu == 95.0
                            assert disk == 60.0
                            mock_slack.assert_called_with(":warning: High CPU usage detected: 95.0%")
                            mock_trigger.assert_called_with("high_cpu")
    
    @pytest.mark.unit
    @patch('monitor.psutil.cpu_percent')
    @patch('monitor.psutil.disk_usage')
    @patch('monitor.psutil.virtual_memory')
    @patch('monitor.send_slack_message')
    @patch('monitor.trigger_remediation')
    def test_check_system_high_disk(self, mock_trigger, mock_slack, mock_memory, mock_disk, mock_cpu):
        """Test system check with high disk usage"""
        mock_cpu.return_value = 50.0
        mock_disk.return_value = MagicMock(percent=95.0)
        mock_memory.return_value = MagicMock(percent=40.0)
        
        cpu, disk = self.monitor.check_system()
        
        assert cpu == 50.0
        assert disk == 95.0
        mock_slack.assert_called_with(":warning: High Disk usage: 95.0%")
        mock_trigger.assert_called_with("high_disk")
    
    @pytest.mark.unit
    @patch('monitor.psutil.cpu_percent')
    @patch('monitor.psutil.disk_usage')
    @patch('monitor.psutil.virtual_memory')
    @patch('monitor.send_slack_message')
    @patch('monitor.trigger_remediation')
    def test_check_system_high_memory(self, mock_trigger, mock_slack, mock_memory, mock_disk, mock_cpu):
        """Test system check with high memory usage"""
        mock_cpu.return_value = 50.0
        mock_disk.return_value = MagicMock(percent=60.0)
        mock_memory.return_value = MagicMock(percent=95.0)
        
        cpu, disk = self.monitor.check_system()
        
        assert cpu == 50.0
        assert disk == 60.0
        mock_slack.assert_called_with(":warning: High Memory usage detected: 95.0%")
        mock_trigger.assert_called_with("high_memory")
    
    @pytest.mark.unit
    @patch('monitor.psutil.cpu_percent')
    @patch('monitor.psutil.disk_usage')
    @patch('monitor.send_slack_message')
    def test_trigger_remediation_success(self, mock_slack, mock_disk, mock_cpu):
        """Test successful remediation trigger"""
        # Setup mocks
        mock_cpu.return_value = 85.0
        mock_disk.return_value = MagicMock(percent=60.0)
        
        # Mock the remediation client that was created at module level
        self.monitor.remediation_client.trigger_remediation = Mock(return_value=True)
        
        # Call trigger_remediation
        self.monitor.trigger_remediation("high_cpu")
        
        # Verify remediation client was called
        self.monitor.remediation_client.trigger_remediation.assert_called_once_with(
            "high_cpu", 
            {"cpu_percent": 85.0, "disk_percent": None}
        )
        
        # Verify success message was sent
        slack_calls = mock_slack.call_args_list
        assert any(":tools: Remediation triggered for high_cpu" in str(call) for call in slack_calls)
    
    @pytest.mark.unit
    @patch('monitor.psutil.cpu_percent')
    @patch('monitor.psutil.disk_usage')
    @patch('monitor.send_slack_message')
    def test_trigger_remediation_failure(self, mock_slack, mock_disk, mock_cpu):
        """Test failed remediation trigger"""
        # Setup mocks
        mock_cpu.return_value = 85.0
        mock_disk.return_value = MagicMock(percent=60.0)
        
        # Mock the remediation client to return False
        self.monitor.remediation_client.trigger_remediation = Mock(return_value=False)
        
        # Call trigger_remediation
        self.monitor.trigger_remediation("high_cpu")
        
        # Verify failure message was sent
        slack_calls = mock_slack.call_args_list
        assert any(":x: Failed to trigger remediation for high_cpu" in str(call) for call in slack_calls)
    
    @pytest.mark.unit
    @patch('monitor.send_slack_message')
    def test_trigger_remediation_exception(self, mock_slack):
        """Test remediation trigger with exception"""
        # Mock the remediation client to raise an exception
        self.monitor.remediation_client.trigger_remediation = Mock(
            side_effect=Exception("Connection error")
        )
        
        # Call trigger_remediation
        self.monitor.trigger_remediation("high_cpu")
        
        # Verify error message was sent
        slack_calls = mock_slack.call_args_list
        assert any(":x: Error triggering remediation: Connection error" in str(call) for call in slack_calls)
    
    @pytest.mark.unit
    def test_thresholds(self):
        """Test that thresholds are properly set from config"""
        assert self.monitor.CPU_THRESHOLD == 90  # Changed to match actual config
        assert self.monitor.DISK_THRESHOLD == 90
        assert self.monitor.MEMORY_THRESHOLD == 90
        assert self.monitor.CHECK_INTERVAL == 60
    
    @pytest.mark.unit
    @patch('monitor.schedule')
    @patch('monitor.time.sleep')
    @patch('monitor.check_system')
    def test_main_function(self, mock_check_system, mock_sleep, mock_schedule):
        """Test the main function sets up scheduling correctly"""
        # Make sleep raise exception to exit the infinite loop
        mock_sleep.side_effect = KeyboardInterrupt
        
        try:
            self.monitor.main()
        except KeyboardInterrupt:
            pass
        
        # Verify initial check was called
        mock_check_system.assert_called_once()
        
        # Verify schedule was set up
        mock_schedule.every.assert_called_once_with(60)
        mock_schedule.every().seconds.do.assert_called_once_with(mock_check_system)
        
        # Verify run_pending was called
        mock_schedule.run_pending.assert_called()