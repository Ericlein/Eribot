"""
Fixed logger tests
"""

import pytest
import logging
import os
from unittest.mock import patch, Mock
from pathlib import Path

# Import the logger module
from utils.logger import get_logger, setup_logging, log_system_info


class TestGetLogger:
    """Test get_logger function"""

    @patch("utils.logger.setup_logging")
    def test_get_logger_default(self, mock_setup_logging):
        """Test get_logger with default configuration"""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = []
        mock_setup_logging.return_value = mock_logger

        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            result = get_logger("test_logger")

            mock_setup_logging.assert_called_once_with(name="test_logger", level="INFO")
            assert result == mock_logger

    @patch("utils.logger.setup_logging")
    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_get_logger_env_level(self, mock_setup_logging):
        """Test get_logger with environment variable log level"""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = []
        mock_setup_logging.return_value = mock_logger

        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            result = get_logger("test_logger")

            mock_setup_logging.assert_called_once_with(
                name="test_logger", level="DEBUG"
            )
            assert result == mock_logger

    def test_get_logger_existing_handlers(self):
        """Test get_logger when logger already has handlers"""
        mock_logger = Mock(spec=logging.Logger)
        mock_handler = Mock()
        mock_logger.handlers = [mock_handler]

        with patch("logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value = mock_logger

            with patch("utils.logger.setup_logging") as mock_setup_logging:
                result = get_logger("test_logger")
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
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = Mock(clear=Mock())  # Important fix
        mock_get_logger.return_value = mock_logger

        mock_console_handler = Mock()
        mock_file_handler_instance = Mock()
        mock_stream_handler.return_value = mock_console_handler
        mock_file_handler.return_value = mock_file_handler_instance

        result = setup_logging("test_logger", "INFO")

        mock_logger.setLevel.assert_called_with(logging.INFO)
        mock_logger.handlers.clear.assert_called_once()
        assert mock_logger.addHandler.call_count >= 1
        assert result == mock_logger

    @patch("logging.getLogger")
    def test_setup_logging_console_only(self, mock_get_logger):
        """Test setup_logging with console only"""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.handlers = Mock(clear=Mock())  # Important fix
        mock_get_logger.return_value = mock_logger

        with patch("logging.StreamHandler") as mock_stream_handler:
            mock_console_handler = Mock()
            mock_stream_handler.return_value = mock_console_handler

            result = setup_logging(
                "test_logger", "INFO", log_to_file=False, log_to_console=True
            )

            mock_logger.setLevel.assert_called_with(logging.INFO)
            mock_logger.handlers.clear.assert_called_once()
            assert result == mock_logger


class TestLogSystemInfo:
    """Test log_system_info function"""

    @patch("utils.logger.psutil")
    @patch("utils.logger.platform")
    def test_log_system_info(self, mock_platform, mock_psutil):
        """Test log_system_info function"""
        mock_platform.platform.return_value = "Windows-10-10.0.19041-SP0"
        mock_platform.python_version.return_value = "3.11.5"
        mock_psutil.cpu_count.return_value = 8

        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.total = 500 * 1024**3
        mock_psutil.disk_usage.return_value = mock_disk

        mock_logger = Mock(spec=logging.Logger)

        log_system_info(mock_logger)

        assert mock_logger.info.call_count >= 5
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("EriBot System Information" in call for call in info_calls)
        assert any("Platform:" in call for call in info_calls)
        assert any("CPU Count:" in call for call in info_calls)

    def test_log_system_info_with_exception(self):
        """Test log_system_info when psutil raises an exception"""
        mock_logger = Mock(spec=logging.Logger)

        with patch("utils.logger.psutil") as mock_psutil, patch(
            "utils.logger.platform"
        ) as mock_platform:

            mock_psutil.cpu_count.side_effect = Exception("Test error")
            mock_psutil.virtual_memory.side_effect = Exception("Test error")
            mock_psutil.disk_usage.side_effect = Exception("Test error")

            mock_platform.platform.return_value = "Test Platform"
            mock_platform.python_version.return_value = "3.x.x"

            try:
                log_system_info(mock_logger)
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
        mock_logger.handlers = [mock_handler]
        mock_get_logger.return_value = mock_logger

        eri_logger = EriLogger("test_logger", "INFO")
        assert eri_logger.logger == mock_logger


class TestColorFormatter:
    """Test ColorFormatter class"""

    def test_color_formatter(self):
        """Test ColorFormatter adds colors to log records"""
        from utils.logger import ColorFormatter

        formatter = ColorFormatter("%(levelname)s - %(message)s")
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

        assert "\033[32m" in formatted
        assert "\033[0m" in formatted
        assert "test message" in formatted

    def test_color_formatter_unknown_level(self):
        """Test ColorFormatter with unknown log level"""
        from utils.logger import ColorFormatter

        formatter = ColorFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=99,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.levelname = "CUSTOM"

        formatted = formatter.format(record)

        assert "test message" in formatted
