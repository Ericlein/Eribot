import logging
import sys
from pathlib import Path

# Add parent directory to path for imports during transition
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import and re-export the existing health checker classes
try:
    from health_checker import (
        HealthStatus,
        SystemHealthChecker,
        ServiceHealthChecker,
        CompositeHealthChecker,
    )

    # Alias for consistency
    HealthChecker = CompositeHealthChecker

except ImportError as e:
    logging.warning(f"Warning: Could not import health_checker: {e}")

    # Fallback minimal implementation
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Dict, Any

    @dataclass
    class HealthStatus:
        is_healthy: bool
        status: str
        timestamp: datetime
        details: Dict[str, Any]
        duration_ms: float = 0.0

    class HealthChecker:
        def __init__(self, *args, **kwargs):
            pass

        def get_overall_health(self):
            return HealthStatus(
                is_healthy=True,
                status="health checker not available",
                timestamp=datetime.now(),
                details={},
                duration_ms=0.0,
            )


__all__ = [
    "HealthStatus",
    "SystemHealthChecker",
    "ServiceHealthChecker",
    "CompositeHealthChecker",
    "HealthChecker",
]
