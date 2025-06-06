"""
Configuration loader for EriBot.
Fixed version with .env file loading.
"""

import yaml
import os
import sys
import logging
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports during transition
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load .env files automatically
try:
    from dotenv import load_dotenv
    
    # Try to load .env from different locations
    env_files = [
        Path('.env'),                    # Current directory
        Path('../.env'),                 # Parent directory  
        Path('../config/.env'),          # Config directory
        current_dir.parent / '.env',     # Relative to this file
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file)
            logging.info(f"Loaded environment from: {env_file}")
            break
    else:
        logging.warning("No .env file found - using system environment variables only")
        
except ImportError:
    logging.warning("python-dotenv not available - using system environment variables only")

from .models import AppConfig, MonitoringConfig, SlackConfig, RemediatorConfig, LoggingConfig

# Use fallback logging and exceptions during transition
def get_logger(name):
    return logging.getLogger(name)

class ConfigurationError(Exception):
    pass

class ValidationError(Exception):
    pass

logger = get_logger("config")


class ConfigLoader:
    """Enhanced configuration loader with better path resolution and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigLoader.
        
        Args:
            config_path: Path to config file. If None, searches common locations.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self._find_config_file()
        
        self._config: Optional[AppConfig] = None

    def _find_config_file(self) -> Path:
        """Find config.yaml in common locations."""
        possible_paths = [
            Path("config/config.yaml"),                    # Relative to current dir
            Path("../config/config.yaml"),                 # Relative to python_monitor
            Path(__file__).parent.parent.parent / "config" / "config.yaml",  # Relative to this file
            Path("/opt/eribot/config/config.yaml"),        # Linux service location
            Path("C:/EriBot/config/config.yaml"),          # Windows service location
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"Found config file: {path}")
                return path
        
        # Default fallback
        default_path = Path("config/config.yaml")
        print(f"Config file not found. Using default: {default_path}")
        return default_path

    def load(self) -> AppConfig:
        """Load configuration from YAML file and environment variables."""
        try:
            # Load YAML config if file exists
            yaml_config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    yaml_config = yaml.safe_load(file) or {}
                print(f"Loaded YAML config from: {self.config_path}")
            else:
                print(f"Config file not found: {self.config_path}. Using environment variables only.")
            
            # Load monitoring config with env var overrides
            monitoring_yaml = yaml_config.get('monitoring', {})
            monitoring_config = MonitoringConfig(
                cpu_threshold=int(os.getenv('CPU_THRESHOLD', monitoring_yaml.get('cpu_threshold', 90))),
                disk_threshold=int(os.getenv('DISK_THRESHOLD', monitoring_yaml.get('disk_threshold', 90))),
                memory_threshold=int(os.getenv('MEMORY_THRESHOLD', monitoring_yaml.get('memory_threshold', 90))),
                check_interval=int(os.getenv('CHECK_INTERVAL', monitoring_yaml.get('check_interval', 60)))
            )
            
            # Load slack config with env var overrides
            slack_yaml = yaml_config.get('slack', {})
            slack_config = SlackConfig(
                channel=os.getenv('SLACK_CHANNEL', slack_yaml.get('channel', '#devops-alerts')),
                token=os.getenv('SLACK_BOT_TOKEN', ''),  # Must be set via env var for security
                username=os.getenv('SLACK_USERNAME', slack_yaml.get('username', 'EriBot')),
                icon_emoji=os.getenv('SLACK_ICON', slack_yaml.get('icon_emoji', ':robot_face:'))
            )
            
            # Load remediator config with env var overrides
            remediator_yaml = yaml_config.get('remediator', {})
            remediator_config = RemediatorConfig(
                url=os.getenv('REMEDIATOR_URL', remediator_yaml.get('url', 'http://localhost:5001')),
                timeout=int(os.getenv('REMEDIATOR_TIMEOUT', remediator_yaml.get('timeout', 30))),
                retry_attempts=int(os.getenv('REMEDIATOR_RETRIES', remediator_yaml.get('retry_attempts', 3)))
            )
            
            # Load logging config with env var overrides
            logging_yaml = yaml_config.get('logging', {})
            logging_config = LoggingConfig(
                level=os.getenv('LOG_LEVEL', logging_yaml.get('level', 'INFO')),
                max_file_size=os.getenv('LOG_MAX_SIZE', logging_yaml.get('max_file_size', '10MB')),
                backup_count=int(os.getenv('LOG_BACKUP_COUNT', logging_yaml.get('backup_count', 5))),
                console_output=os.getenv('LOG_CONSOLE', str(logging_yaml.get('console_output', True))).lower() in ('true', '1', 'yes')
            )
            
            self._config = AppConfig(
                monitoring=monitoring_config,
                slack=slack_config,
                remediator=remediator_config,
                logging=logging_config
            )
            
            print("Configuration loaded successfully")
            print(f"Config: CPU={monitoring_config.cpu_threshold}%, "
                  f"Disk={monitoring_config.disk_threshold}%, "
                  f"Memory={monitoring_config.memory_threshold}%, "
                  f"Interval={monitoring_config.check_interval}s")
            
            return self._config
            
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file {self.config_path} not found")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {e}")
        except ValueError as e:
            raise ConfigurationError(f"Error converting configuration values: {e}")
        except Exception as e:
            raise ConfigurationError(f"Unexpected error loading configuration: {e}")

    def validate(self) -> bool:
        """Validate configuration values."""
        if not self._config:
            print("Configuration not loaded")
            return False
        
        errors = []
        
        # Check required environment variables
        if not self._config.slack.token:
            errors.append("SLACK_BOT_TOKEN environment variable is required")
        
        if self._config.slack.token and not self._config.slack.token.startswith('xoxb-'):
            errors.append("SLACK_BOT_TOKEN must be a valid bot token (starts with 'xoxb-')")
        
        # Validate thresholds (1-100%)
        if not (1 <= self._config.monitoring.cpu_threshold <= 100):
            errors.append(f"CPU threshold must be between 1 and 100, got {self._config.monitoring.cpu_threshold}")
        
        if not (1 <= self._config.monitoring.memory_threshold <= 100):
            errors.append(f"Memory threshold must be between 1 and 100, got {self._config.monitoring.memory_threshold}")
            
        if not (1 <= self._config.monitoring.disk_threshold <= 100):
            errors.append(f"Disk threshold must be between 1 and 100, got {self._config.monitoring.disk_threshold}")
        
        # Validate check interval (5 seconds to 1 hour)
        if not (5 <= self._config.monitoring.check_interval <= 3600):
            errors.append(f"Check interval must be between 5 and 3600 seconds, got {self._config.monitoring.check_interval}")
        
        # Validate Slack channel format
        if not self._config.slack.channel.startswith('#'):
            errors.append(f"Slack channel must start with '#', got {self._config.slack.channel}")
        
        # Validate remediator URL
        if not self._config.remediator.url.startswith(('http://', 'https://')):
            errors.append(f"Remediator URL must start with http:// or https://, got {self._config.remediator.url}")
        
        # Validate logging level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config.logging.level.upper() not in valid_levels:
            errors.append(f"Log level must be one of {valid_levels}, got {self._config.logging.level}")
        
        # Log all errors
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return False
        
        print("Configuration validation passed")
        return True

    def get_config(self) -> Optional[AppConfig]:
        """Get the loaded configuration."""
        return self._config


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Convenience function to load and validate configuration.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        AppConfig instance
        
    Raises:
        ConfigurationError: If config loading or validation fails
    """
    loader = ConfigLoader(config_path)
    config = loader.load()
    
    if not loader.validate():
        raise ConfigurationError("Configuration validation failed")
    
    return config