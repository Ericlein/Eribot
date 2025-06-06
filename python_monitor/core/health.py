
"""
Health checking functionality for EriBot.

Moved from health_checker.py with minimal changes for now.
"""

# Import and re-export the existing health checker classes
# We'll keep the existing implementation for now since it's working well
from python_monitor.health_checker import (
    HealthStatus,
    SystemHealthChecker,
    ServiceHealthChecker,
    CompositeHealthChecker
)

# Alias for consistency
HealthChecker = CompositeHealthChecker

__all__ = [
    "HealthStatus",
    "SystemHealthChecker", 
    "ServiceHealthChecker",
    "CompositeHealthChecker",
    "HealthChecker",
]