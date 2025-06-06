"""
EriBot Python Monitor Package

A system monitoring and auto-remediation service that integrates with Slack
and provides automated responses to system issues.
"""

__version__ = "2.0.0"
__author__ = "Eric S"

from .config import load_config, AppConfig
from .core.monitor import SystemMonitor

__all__ = [
    "load_config",
    "AppConfig",
    "SystemMonitor",
    "__version__",
]
