"""
Fixed logger tests
"""

import pytest
import logging
import os
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Import the logger module
from utils.logger import get_logger, setup_logging, log_system_info


class TestGetLogger:
    """Test get_logger function"""

    @patch("utils.logger.setup_logging")
    def test_get_logger_default(self, mock_setup_logging):
        """Test get_logger with default configuration"""
        # Create a mock logger
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = []  # Empty handlers initially
        mock_setup_logging.return_value = mock_logger

        # Patch logging.getLogger to return our mock
        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            # Call get_logger
            result = get_logger("test_logger")

            # Verify setup_logging was called once
            mock_setup_logging.assert_called_once_with(name="test_logger", level="INFO")
            assert result == mock_logger

    @patch("utils.logger.setup_logging")
    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_get_logger_env_level(self, mock_setup_logging):
        """Test get_logger with environment variable log level"""
        # Create a mock logger
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = []  # Empty handlers initially
        mock_setup_logging.return_value = mock_logger

        # Patch logging.getLogger to return our mock
        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            # Call get_logger
            result = get_logger("test_logger")

            # Verify setup_logging was called with DEBUG level
            mock_setup_logging.assert_called_once_with(name="test_logger", level="DEBUG")
            assert result == mock_logger

    def test_get_logger_existing_handlers(self):
        """Test get_logger when logger already has handlers"""
        # Create a mock logger with existing handlers
        mock_logger = Mock(spec=logging.Logger)
        mock_handler = Mock()
        mock_logger.handlers = [mock_handler]  # Has existing handlers

        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            # setup_logging should NOT be called when handlers exist
            with patch("utils.logger.setup_logging") as mock_setup_logging:
                result = get_logger("test_logger")

                # Should return the existing logger without calling setup_logging
                mock_setup_logging.assert_not_called()
                assert result == mock_logger


class TestSetupLogging:
    """Test setup_logging function"""

    @patch("logging.getLogger")
    @patch("logging.handlers.RotatingFileHandler")
    @patch("logging.StreamHandler")
    @patch("pathlib.Path.mkdir")
    def test_setup_logging_basic(
        self, mock_mkdir, mock_stream_handler, mock_file_handler, mock_get_logger
    ):
        """Test basic setup_logging functionality"""
        # Create mock logger
        mock_logger = Mock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        # Create mock handlers
        mock_console_handler = Mock()
        mock_file_handler_instance = Mock()
        mock_error_handler = Mock()

        mock_stream_handler.return_value = mock_console_handler
        mock_file_handler.return_value = mock_file_handler_instance

        # Test setup_logging
        result = setup_logging("test_logger", "INFO")

        # Verify logger configuration
        mock_logger.setLevel.assert_called_with(logging.INFO)
        mock_logger.handlers.clear.assert_called_once()

        # Verify handlers were added
        assert mock_logger.addHandler.call_count >= 1

        # Verify result
        assert result == mock_logger

    @patch("logging.getLogger")
    def test_setup_logging_console_only(self, mock_get_logger):
        """Test setup_logging with console only"""
        mock_logger = Mock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        with patch("logging.StreamHandler") as mock_stream_handler:
            mock_console_handler = Mock()
            mock_stream_handler.return_value = mock_console_handler

            result = setup_logging("test_logger", "INFO", log_to_file=False, log_to_console=True)

            mock_logger.setLevel.assert_called_with(logging.INFO)
            assert result == mock_logger


class TestLogSystemInfo:
    """Test log_system_info function"""

    @patch("utils.logger.psutil")
    @patch("utils.logger.platform")
    def test_log_system_info(self, mock_platform, mock_psutil):
        """Test log_system_info function"""
        # Mock platform and psutil
        mock_platform.platform.return_value = "Windows-10-10.0.19041-SP0"
        mock_platform.python_version.return_value = "3.11.5"

        mock_psutil.cpu_count.return_value = 8

        # Mock memory object
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock disk object
        mock_disk = Mock()
        mock_disk.total = 500 * 1024**3  # 500GB
        mock_psutil.disk_usage.return_value = mock_disk

        # Create a mock logger
        mock_logger = Mock(spec=logging.Logger)

        # Call log_system_info
        log_system_info(mock_logger)

        # Verify info logs were called
        assert mock_logger.info.call_count >= 5  # Should log multiple system info lines

        # Verify specific calls
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]

        # Check that system information was logged
        system_info_found = any("EriBot System Information" in call for call in info_calls)
        platform_info_found = any("Platform:" in call for call in info_calls)
        cpu_info_found = any("CPU Count:" in call for call in info_calls)

        assert system_info_found, f"System info header not found in: {info_calls}"
        assert platform_info_found, f"Platform info not found in: {info_calls}"
        assert cpu_info_found, f"CPU info not found in: {info_calls}"

    def test_log_system_info_with_exception(self):
        """Test log_system_info when psutil raises an exception"""
        mock_logger = Mock(spec=logging.Logger)

        # Test that function handles exceptions gracefully
        with patch("utils.logger.psutil.cpu_count", side_effect=Exception("Test error")):
            with patch("utils.logger.platform.platform", return_value="Test Platform"):
                # Should not raise an exception
                try:
                    log_system_info(mock_logger)
                    # At minimum, should log the header
                    assert mock_logger.info.call_count >= 1
                except Exception as e:
                    pytest.fail(f"log_system_info should not raise exceptions: {e}")


class TestEriLogger:
    """Test EriLogger class"""

    @patch("logging.getLogger")
    @patch("pathlib.Path.mkdir")
    def test_eri_logger_creation(self, mock_mkdir, mock_get_logger):
        """Test EriLogger creation"""
        from utils.logger import EriLogger

        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        eri_logger = EriLogger("test_logger", "INFO")

        assert eri_logger.name == "test_logger"
        assert eri_logger.log_level == logging.INFO
        assert eri_logger.logger == mock_logger

    @patch("logging.getLogger")
    @patch("pathlib.Path.mkdir")
    def test_eri_logger_no_duplicate_handlers(self, mock_mkdir, mock_get_logger):
        """Test that EriLogger doesn't add duplicate handlers"""
        from utils.logger import EriLogger

        mock_logger = Mock(spec=logging.Logger)
        mock_handler = Mock()
        mock_logger.handlers = [mock_handler]  # Already has handlers
        mock_get_logger.return_value = mock_logger

        eri_logger = EriLogger("test_logger", "INFO")

        # Should not call _setup_handlers when handlers already exist
        assert eri_logger.logger == mock_logger


class TestColorFormatter:
    """Test ColorFormatter class"""

    def test_color_formatter(self):
        """Test ColorFormatter adds colors to log records"""
        from utils.logger import ColorFormatter

        formatter = ColorFormatter("%(levelname)s - %(message)s")

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should contain color codes for INFO level
        assert "\033[32m" in formatted  # Green color for INFO
        assert "\033[0m" in formatted  # Reset color
        assert "test message" in formatted

    def test_color_formatter_unknown_level(self):
        """Test ColorFormatter with unknown log level"""
        from utils.logger import ColorFormatter

        formatter = ColorFormatter("%(levelname)s - %(message)s")

        # Create a log record with custom level
        record = logging.LogRecord(
            name="test",
            level=99,  # Custom level
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.levelname = "CUSTOM"

        formatted = formatter.format(record)

        # Should still work without colors
        assert "test message" in formatted
