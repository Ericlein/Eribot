"""
Logging configuration module for EriBot
"""

import logging
import logging.handlers
import sys
from pathlib import Path


class ColorFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        if hasattr(record, "levelname"):
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class EriLogger:
    """Enhanced logger for EriBot with file rotation and formatting"""

    def __init__(self, name: str = "eribot", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up console and file handlers"""

        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)

        console_format = ColorFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(self.log_level)

        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)

        # Error handler (separate file for errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{self.name}-error.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger


def setup_logging(
    name: str = "eribot",
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Set up logging configuration for EriBot

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = ColorFormatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handlers
    if log_to_file:
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Main log file
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{name}-error.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)

    return logger


def log_system_info(logger: logging.Logger):
    """Log system information at startup"""
    import platform
    import psutil

    logger.info("=" * 50)
    logger.info("EriBot System Information")
    logger.info("=" * 50)
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"CPU Count: {psutil.cpu_count()}")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    logger.info(f"Disk: {psutil.disk_usage('/').total / (1024**3):.1f} GB")
    logger.info("=" * 50)


def get_logger(name: str = "eribot") -> logging.Logger:
    """Get or create a logger with default EriBot configuration"""

    # Check if logger already exists and is configured
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return setup_logging(name=name, level=log_level)


# Module-level logger for convenience
logger = get_logger("eribot")
