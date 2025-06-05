"""
EriBot System Monitor
Main monitoring module that checks system resources and triggers alerts/remediation
"""

import time
import psutil
import schedule
from slack_client import send_slack_message
from config_loader import ConfigLoader
from remediation_client import RemediationClient
from dotenv import load_dotenv 

# Load configuration
load_dotenv()
config_loader = ConfigLoader()
config = config_loader.load()

# Validate configuration
if not config_loader.validate():
    raise ValueError("Invalid configuration")

CPU_THRESHOLD = config.monitoring.cpu_threshold
DISK_THRESHOLD = config.monitoring.disk_threshold
MEMORY_THRESHOLD = config.monitoring.memory_threshold
CHECK_INTERVAL = config.monitoring.check_interval

# Initialize remediation client
remediation_client = RemediationClient(config.remediator)


def check_system():
    """Check system metrics and trigger alerts if thresholds exceeded"""
    cpu_percent = psutil.cpu_percent(interval=1)
    disk_usage = psutil.disk_usage('/')
    memory = psutil.virtual_memory().percent
    
    if cpu_percent > CPU_THRESHOLD:
        message = f":warning: High CPU usage detected: {cpu_percent}%"
        send_slack_message(message)
        trigger_remediation("high_cpu")

    if memory > MEMORY_THRESHOLD:
        send_slack_message(f":warning: High Memory usage detected: {memory}%")
        trigger_remediation("high_memory")
    
    if disk_usage.percent > DISK_THRESHOLD:
        message = f":warning: High Disk usage: {disk_usage.percent}%"
        send_slack_message(message)
        trigger_remediation("high_disk")
    
    return cpu_percent, disk_usage.percent


def trigger_remediation(issue_type):
    """Trigger remediation action for the given issue type"""
    try:
        context = {
            "cpu_percent": psutil.cpu_percent() if issue_type == "high_cpu" else None,
            "disk_percent": psutil.disk_usage('/').percent if issue_type == "high_disk" else None,
        }
        
        result = remediation_client.trigger_remediation(issue_type, context)
        
        if result:
            send_slack_message(f":tools: Remediation triggered for {issue_type}")
        else:
            send_slack_message(f":x: Failed to trigger remediation for {issue_type}")
            
    except Exception as e:
        send_slack_message(f":x: Error triggering remediation: {str(e)}")


def main():
    """Main monitoring loop"""
    print(f"Starting system monitoring...")
    print(f"CPU Threshold: {CPU_THRESHOLD}%")
    print(f"Disk Threshold: {DISK_THRESHOLD}%")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    
    # Schedule regular checks
    schedule.every(CHECK_INTERVAL).seconds.do(check_system)
    
    # Initial check
    check_system()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()