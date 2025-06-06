"""
Health checking module for EriBot Python monitoring service
"""

import time
import socket
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from utils.logger import get_logger
from utils.exceptions import ServiceUnavailableError, NetworkError


@dataclass
class HealthStatus:
    """Health status data class"""

    is_healthy: bool
    status: str
    timestamp: datetime
    details: Dict[str, Any]
    duration_ms: float = 0.0


class SystemHealthChecker:
    """Health checker for system resources and services"""

    def __init__(self):
        self.logger = get_logger("health_checker")
        self.start_time = datetime.now()
        self.check_count = 0
        self.last_check = None

    def check_system_health(self) -> HealthStatus:
        """
        Perform comprehensive system health check

        Returns:
            HealthStatus object with overall system health
        """
        start_time = time.time()
        self.check_count += 1
        self.last_check = datetime.now()

        try:
            details = {}
            issues = []

            # Check CPU
            cpu_status = self._check_cpu()
            details["cpu"] = cpu_status
            if not cpu_status["healthy"]:
                issues.append(f"CPU: {cpu_status['status']}")

            # Check Memory
            memory_status = self._check_memory()
            details["memory"] = memory_status
            if not memory_status["healthy"]:
                issues.append(f"Memory: {memory_status['status']}")

            # Check Disk
            disk_status = self._check_disk()
            details["disk"] = disk_status
            if not disk_status["healthy"]:
                issues.append(f"Disk: {disk_status['status']}")

            # Check Network
            network_status = self._check_network()
            details["network"] = network_status
            if not network_status["healthy"]:
                issues.append(f"Network: {network_status['status']}")

            # Overall status
            is_healthy = len(issues) == 0
            status = "healthy" if is_healthy else f"unhealthy: {'; '.join(issues)}"

            details.update(
                {
                    "uptime_seconds": (
                        datetime.now() - self.start_time
                    ).total_seconds(),
                    "check_count": self.check_count,
                    "hostname": psutil.cpu_count(),
                    "platform": psutil.cpu_count(),  # This will be fixed in actual implementation
                }
            )

            duration_ms = (time.time() - start_time) * 1000

            return HealthStatus(
                is_healthy=is_healthy,
                status=status,
                timestamp=self.last_check,
                details=details,
                duration_ms=duration_ms,
            )

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            duration_ms = (time.time() - start_time) * 1000

            return HealthStatus(
                is_healthy=False,
                status=f"health check failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)},
                duration_ms=duration_ms,
            )

    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Get load average on Unix systems
            load_avg = None
            try:
                import os

                if hasattr(os, "getloadavg"):
                    load_avg = os.getloadavg()
            except:
                pass

            # Determine health status
            healthy = cpu_percent < 90  # Consider unhealthy if > 90%
            status = "normal" if healthy else f"high usage: {cpu_percent}%"

            return {
                "healthy": healthy,
                "status": status,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "load_average": load_avg,
            }

        except Exception as e:
            return {"healthy": False, "status": f"check failed: {e}", "error": str(e)}

    def _check_memory(self) -> Dict[str, Any]:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Determine health status
            healthy = memory.percent < 90  # Consider unhealthy if > 90%
            status = "normal" if healthy else f"high usage: {memory.percent}%"

            return {
                "healthy": healthy,
                "status": status,
                "percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "swap_percent": swap.percent,
            }

        except Exception as e:
            return {"healthy": False, "status": f"check failed: {e}", "error": str(e)}

    def _check_disk(self) -> Dict[str, Any]:
        """Check disk health"""
        try:
            disk = psutil.disk_usage("/")

            # Determine health status
            healthy = disk.percent < 90  # Consider unhealthy if > 90%
            status = "normal" if healthy else f"high usage: {disk.percent}%"

            # Check for additional disk issues
            warnings = []
            if disk.free < 1024**3:  # Less than 1GB free
                warnings.append("critically low free space")

            return {
                "healthy": healthy,
                "status": status,
                "percent": disk.percent,
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "warnings": warnings,
            }

        except Exception as e:
            return {"healthy": False, "status": f"check failed: {e}", "error": str(e)}

    def _check_network(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Test basic connectivity
            import socket

            # Try to connect to a reliable external service
            test_hosts = [
                ("8.8.8.8", 53),  # Google DNS
                ("1.1.1.1", 53),  # Cloudflare DNS
                ("google.com", 80),  # Google HTTP
            ]

            successful_connections = 0
            connection_times = []

            for host, port in test_hosts:
                try:
                    start_time = time.time()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()

                    if result == 0:
                        successful_connections += 1
                        connection_times.append((time.time() - start_time) * 1000)

                except Exception:
                    pass

            # Determine health status
            healthy = successful_connections > 0

            if successful_connections == len(test_hosts):
                status = "all connections successful"
            elif successful_connections > 0:
                status = (
                    f"{successful_connections}/{len(test_hosts)} connections successful"
                )
            else:
                status = "no external connectivity"

            avg_latency = (
                sum(connection_times) / len(connection_times)
                if connection_times
                else None
            )

            return {
                "healthy": healthy,
                "status": status,
                "successful_connections": successful_connections,
                "total_tests": len(test_hosts),
                "average_latency_ms": round(avg_latency, 2) if avg_latency else None,
            }

        except Exception as e:
            return {"healthy": False, "status": f"check failed: {e}", "error": str(e)}


class ServiceHealthChecker:
    """Health checker for external services and dependencies"""

    def __init__(self, remediator_url: str = "http://localhost:5001"):
        self.logger = get_logger("service_health")
        self.remediator_url = remediator_url.rstrip("/")

    def check_remediator_service(self, timeout: float = 10.0) -> HealthStatus:
        """
        Check if the remediator service is healthy

        Args:
            timeout: Request timeout in seconds

        Returns:
            HealthStatus for the remediator service
        """
        start_time = time.time()

        try:
            # Try to hit the health endpoint
            health_url = f"{self.remediator_url}/health"

            response = requests.get(health_url, timeout=timeout)
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                try:
                    data = response.json()
                    return HealthStatus(
                        is_healthy=True,
                        status="service responding",
                        timestamp=datetime.now(),
                        details={
                            "url": health_url,
                            "status_code": response.status_code,
                            "response_time_ms": round(duration_ms, 2),
                            "service_data": data,
                        },
                        duration_ms=duration_ms,
                    )
                except:
                    # Response not JSON, but service is responding
                    return HealthStatus(
                        is_healthy=True,
                        status="service responding (non-JSON)",
                        timestamp=datetime.now(),
                        details={
                            "url": health_url,
                            "status_code": response.status_code,
                            "response_time_ms": round(duration_ms, 2),
                        },
                        duration_ms=duration_ms,
                    )
            else:
                return HealthStatus(
                    is_healthy=False,
                    status=f"service returned status {response.status_code}",
                    timestamp=datetime.now(),
                    details={
                        "url": health_url,
                        "status_code": response.status_code,
                        "response_time_ms": round(duration_ms, 2),
                    },
                    duration_ms=duration_ms,
                )

        except requests.exceptions.ConnectionError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                status="connection failed",
                timestamp=datetime.now(),
                details={
                    "url": f"{self.remediator_url}/health",
                    "error": "connection_refused",
                    "response_time_ms": round(duration_ms, 2),
                },
                duration_ms=duration_ms,
            )

        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                status=f"timeout after {timeout}s",
                timestamp=datetime.now(),
                details={
                    "url": f"{self.remediator_url}/health",
                    "error": "timeout",
                    "timeout_seconds": timeout,
                    "response_time_ms": round(duration_ms, 2),
                },
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                status=f"unexpected error: {str(e)}",
                timestamp=datetime.now(),
                details={
                    "url": f"{self.remediator_url}/health",
                    "error": str(e),
                    "response_time_ms": round(duration_ms, 2),
                },
                duration_ms=duration_ms,
            )

    def check_slack_connectivity(self, token: str) -> HealthStatus:
        """
        Check Slack API connectivity

        Args:
            token: Slack bot token

        Returns:
            HealthStatus for Slack connectivity
        """
        start_time = time.time()

        try:
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            client = WebClient(token=token)
            response = client.auth_test()

            duration_ms = (time.time() - start_time) * 1000

            return HealthStatus(
                is_healthy=True,
                status="slack api accessible",
                timestamp=datetime.now(),
                details={
                    "user": response.get("user", "unknown"),
                    "team": response.get("team", "unknown"),
                    "response_time_ms": round(duration_ms, 2),
                },
                duration_ms=duration_ms,
            )

        except SlackApiError as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                status=f"slack api error: {e.response['error']}",
                timestamp=datetime.now(),
                details={
                    "error": e.response["error"],
                    "response_time_ms": round(duration_ms, 2),
                },
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                status=f"slack connectivity failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e), "response_time_ms": round(duration_ms, 2)},
                duration_ms=duration_ms,
            )


class CompositeHealthChecker:
    """Composite health checker that combines system and service checks"""

    def __init__(
        self, remediator_url: str = "http://localhost:5001", slack_token: str = ""
    ):
        self.system_checker = SystemHealthChecker()
        self.service_checker = ServiceHealthChecker(remediator_url)
        self.slack_token = slack_token
        self.logger = get_logger("composite_health")

    def check_all_health(self) -> Dict[str, HealthStatus]:
        """
        Check health of all components

        Returns:
            Dictionary of component health statuses
        """
        results = {}

        # System health
        results["system"] = self.system_checker.check_system_health()

        # Remediator service health
        results["remediator"] = self.service_checker.check_remediator_service()

        # Slack connectivity (if token provided)
        if self.slack_token:
            results["slack"] = self.service_checker.check_slack_connectivity(
                self.slack_token
            )

        return results

    def get_overall_health(self) -> HealthStatus:
        """
        Get overall health status based on all components

        Returns:
            Combined health status
        """
        start_time = time.time()

        component_statuses = self.check_all_health()

        # Determine overall health
        all_healthy = all(status.is_healthy for status in component_statuses.values())

        unhealthy_components = [
            name for name, status in component_statuses.items() if not status.is_healthy
        ]

        if all_healthy:
            status = "all components healthy"
        else:
            status = f"unhealthy components: {', '.join(unhealthy_components)}"

        duration_ms = (time.time() - start_time) * 1000

        return HealthStatus(
            is_healthy=all_healthy,
            status=status,
            timestamp=datetime.now(),
            details={
                "components": {
                    name: {
                        "healthy": status.is_healthy,
                        "status": status.status,
                        "timestamp": status.timestamp.isoformat(),
                    }
                    for name, status in component_statuses.items()
                }
            },
            duration_ms=duration_ms,
        )
