"""
Configuration data models for EriBot.

Contains all the dataclasses that define the configuration structure.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MonitoringConfig:
    """Configuration for system monitoring."""
    cpu_threshold: int
    disk_threshold: int
    memory_threshold: int
    check_interval: int


@dataclass  
class SlackConfig:
    """Configuration for Slack integration."""
    channel: str
    token: str
    username: str = "EriBot"
    icon_emoji: str = ":robot_face:"


@dataclass
class RemediatorConfig:
    """Configuration for remediation service."""
    url: str
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    max_file_size: str = "10MB"
    backup_count: int = 5
    console_output: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    monitoring: MonitoringConfig
    slack: SlackConfig
    remediator: RemediatorConfig
    logging: LoggingConfig