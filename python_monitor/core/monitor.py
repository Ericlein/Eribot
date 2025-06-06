import time
import psutil
import schedule
import threading
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

import sys
from pathlib import Path

# Add parent directory to path for imports during transition
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from config.models import AppConfig
from clients.slack import SlackClient
from clients.remediation import RemediationClient

def get_logger(name):
    import logging
    return logging.getLogger(name)

class MonitoringError(Exception):
    pass

class ThresholdExceededError(Exception):
    pass

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    timestamp: datetime
    hostname: str

@dataclass
class AlertContext:
    metric_name: str
    current_value: float
    threshold: float
    metrics: SystemMetrics

class SystemMonitor:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = get_logger('system_monitor')
        
        # Initialize clients
        try:
            self.slack_client = SlackClient(config.slack)
            self.remediation_client = RemediationClient(config.remediator)
        except Exception as e:
            raise MonitoringError(f'Failed to initialize clients: {e}')
        
        # Monitor state
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self.start_time = datetime.now()
        self.check_count = 0
        self.alert_count = 0
        self.remediation_count = 0
        
        self.logger.info('System monitor initialized')
    
    def start(self) -> None:
        if self._running:
            self.logger.warning('Monitor is already running')
            return
        
        self._running = True
        self._stop_event.clear()
        
        self.logger.info('Starting system monitoring...')
        
        # Schedule regular checks
        schedule.every(self.config.monitoring.check_interval).seconds.do(self._check_system_wrapper)
        
        # Perform initial check
        self._check_system_wrapper()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        # Send startup notification
        try:
            self.slack_client.send_message(
                f' EriBot monitoring started on {psutil.cpu_count()} CPU system',
                severity='info'
            )
        except Exception as e:
            self.logger.warning(f'Could not send startup notification: {e}')
        
        # Keep main thread alive
        self._keep_alive()
    
    def stop(self) -> None:
        if not self._running:
            return
        
        self.logger.info('Stopping system monitoring...')
        self._running = False
        self._stop_event.set()
        
        # Clear schedule
        schedule.clear()
        
        # Wait for thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        # Send shutdown notification
        try:
            uptime = datetime.now() - self.start_time
            self.slack_client.send_message(
                f' EriBot monitoring stopped. '
                f'Uptime: {uptime}, Checks: {self.check_count}, Alerts: {self.alert_count}',
                severity='info'
            )
        except Exception as e:
            self.logger.warning(f'Could not send shutdown notification: {e}')
        
        self.logger.info('System monitoring stopped')
    
    def _monitoring_loop(self) -> None:
        while self._running and not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'Error in monitoring loop: {e}')
                time.sleep(5)
    
    def _keep_alive(self) -> None:
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('Received interrupt signal')
            self.stop()
    
    def _check_system_wrapper(self) -> None:
        try:
            self.check_system()
        except Exception as e:
            self.logger.error(f'System check failed: {e}')
            try:
                self.slack_client.send_error_message(
                    f'System check failed: {str(e)}'
                )
            except Exception as e:
                self.logger.warning(f'Failed to send error notification: {e}')
    
    def check_system(self) -> SystemMetrics:
        start_time = time.time()
        self.check_count += 1
        
        try:
            # Gather system metrics
            metrics = self._gather_metrics()
            
            self.logger.debug(
                f'System check #{self.check_count}: '
                f'CPU={metrics.cpu_percent:.1f}%, '
                f'Memory={metrics.memory_percent:.1f}%, '
                f'Disk={metrics.disk_percent:.1f}%'
            )
            
            # Check thresholds and trigger alerts
            self._check_thresholds(metrics)
            
            # Log performance
            duration = (time.time() - start_time) * 1000
            self.logger.debug(f'System check completed in {duration:.1f}ms')
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error during system check: {e}')
            raise MonitoringError(f'System check failed: {e}')
    
    def _gather_metrics(self) -> SystemMetrics:
        try:
            # Get CPU usage (1 second interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Get hostname
            hostname = socket.gethostname()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                timestamp=datetime.now(),
                hostname=hostname
            )
            
        except Exception as e:
            raise MonitoringError(f'Failed to gather system metrics: {e}')
    
    def _check_thresholds(self, metrics: SystemMetrics) -> None:
        alerts_triggered = []
        
        # Check CPU threshold
        if metrics.cpu_percent > self.config.monitoring.cpu_threshold:
            alert_context = AlertContext('CPU', metrics.cpu_percent, self.config.monitoring.cpu_threshold, metrics)
            alerts_triggered.append(alert_context)
        
        # Check memory threshold
        if metrics.memory_percent > self.config.monitoring.memory_threshold:
            alert_context = AlertContext('Memory', metrics.memory_percent, self.config.monitoring.memory_threshold, metrics)
            alerts_triggered.append(alert_context)
        
        # Check disk threshold
        if metrics.disk_percent > self.config.monitoring.disk_threshold:
            alert_context = AlertContext('Disk', metrics.disk_percent, self.config.monitoring.disk_threshold, metrics)
            alerts_triggered.append(alert_context)
        
        # Process alerts
        for alert in alerts_triggered:
            self._handle_threshold_alert(alert)
    
    def _handle_threshold_alert(self, alert: AlertContext) -> None:
        self.alert_count += 1
        
        # Send Slack alert
        message = (
            f'High {alert.metric_name} usage detected: {alert.current_value:.1f}% '
            f'(threshold: {alert.threshold}%)'
        )
        
        try:
            self.slack_client.send_alert(message, severity='warning')
        except Exception as e:
            self.logger.error(f'Failed to send Slack alert: {e}')
        
        # Trigger remediation
        issue_type = f'high_{alert.metric_name.lower()}'
        self._trigger_remediation(issue_type, alert)
    
    def _trigger_remediation(self, issue_type: str, alert: AlertContext) -> None:
        try:
            # Prepare context
            context = {
                'hostname': alert.metrics.hostname,
                'timestamp': alert.metrics.timestamp.isoformat(),
                f'{alert.metric_name.lower()}_percent': alert.current_value,
                'threshold': alert.threshold
            }
            
            self.logger.info(f'Triggering remediation for: {issue_type}')
            
            # Attempt remediation
            success = self.remediation_client.trigger_remediation(issue_type, context)
            
            if success:
                self.remediation_count += 1
                self.slack_client.send_success_message(
                    f'Remediation triggered for {issue_type}'
                )
            else:
                self.slack_client.send_error_message(
                    f'Failed to trigger remediation for {issue_type}'
                )
                
        except Exception as e:
            error_msg = f'Remediation failed for {issue_type}: {str(e)}'
            self.logger.error(error_msg)
            self.slack_client.send_error_message(error_msg)
    
    def get_status(self) -> Dict[str, Any]:
        uptime = datetime.now() - self.start_time
        
        return {
            'running': self._running,
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],
            'check_count': self.check_count,
            'alert_count': self.alert_count,
            'remediation_count': self.remediation_count,
            'config': {
                'cpu_threshold': self.config.monitoring.cpu_threshold,
                'memory_threshold': self.config.monitoring.memory_threshold,
                'disk_threshold': self.config.monitoring.disk_threshold,
                'check_interval': self.config.monitoring.check_interval
            }
        }
    
    def send_health_report(self) -> None:
        try:
            metrics = self._gather_metrics()
            self.slack_client.send_system_health_report(
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_percent
            )
        except Exception as e:
            self.logger.error(f'Failed to send health report: {e}')
