"""
EriBot System Monitor Entry Point

This is the main entry point for the EriBot monitoring service.
Replaces the global execution in the old monitor.py.
"""

import sys
import signal
import time
from pathlib import Path
from typing import Optional

# Use absolute imports
from python_monitor.core.monitor import SystemMonitor
from python_monitor.config import load_config
from python_monitor.utils.logger import setup_logging
from python_monitor.utils.exceptions import ErioBotException, ConfigurationError


def setup_signal_handlers(monitor: SystemMonitor) -> None:
    """Set up graceful shutdown signal handlers."""
    def signal_handler(signum: int, frame) -> None:
        signal_name = signal.Signals(signum).name
        print(f"\n🛑 Received {signal_name} signal, shutting down gracefully...")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request


def main(config_path: Optional[str] = None) -> None:
    """
    Main entry point for EriBot System Monitor.
    
    Args:
        config_path: Optional path to configuration file
    """
    logger = None
    monitor = None
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Setup logging
        logger = setup_logging(
            name="eribot",
            level=config.logging.level,
            log_to_file=True,
            log_to_console=config.logging.console_output
        )
        
        logger.info("🤖 Starting EriBot System Monitor v1.0.0")
        logger.info(f"Configuration loaded from: {config_path or 'default locations'}")
        
        # Create and configure monitor
        monitor = SystemMonitor(config)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(monitor)
        
        # Log system information
        from python_monitor.utils.logger import log_system_info
        log_system_info(logger)
        
        # Start monitoring
        logger.info("✅ Starting system monitoring...")
        logger.info(f"CPU Threshold: {config.monitoring.cpu_threshold}%")
        logger.info(f"Memory Threshold: {config.monitoring.memory_threshold}%") 
        logger.info(f"Disk Threshold: {config.monitoring.disk_threshold}%")
        logger.info(f"Check Interval: {config.monitoring.check_interval}s")
        logger.info(f"Slack Channel: {config.slack.channel}")
        
        # Start the monitoring loop
        monitor.start()
        
    except ConfigurationError as e:
        error_msg = f"❌ Configuration Error: {e.message}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)
        
    except ErioBotException as e:
        error_msg = f"❌ EriBot Error: {e.message}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)
        
    except KeyboardInterrupt:
        # This should be handled by signal handlers, but just in case
        if logger:
            logger.info("🛑 Interrupted by user")
        if monitor:
            monitor.stop()
        sys.exit(0)
        
    except Exception as e:
        error_msg = f"💥 Unexpected error: {str(e)}"
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Support command line config path
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        if not Path(config_path).exists():
            print(f"❌ Config file not found: {config_path}", file=sys.stderr)
            sys.exit(1)
    
    main(config_path)