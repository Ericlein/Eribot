import psutil
import time
from slack_client import send_slack_message
import requests
import logging
from typing import Tuple

# Constants
REMEDIATOR_URL = "http://localhost:5001/remediate"
CPU_THRESHOLD = 85
DISK_THRESHOLD = 90
CHECK_INTERVAL = 60

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_system() -> Tuple[float, float]:
    """
    Monitor system CPU and disk usage.
    Returns: Tuple of (cpu_percent, disk_percent)
    """
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/').percent
    
    logger.info(f"System stats - CPU: {cpu}%, Disk: {disk}%")

    if cpu > CPU_THRESHOLD:
        send_slack_message(f":warning: High CPU usage detected: {cpu}%")
        trigger_remediation("high_cpu")

    if disk > DISK_THRESHOLD:
        send_slack_message(f":warning: High Disk usage: {disk}%")
        trigger_remediation("high_disk")
    
    return cpu, disk

def trigger_remediation(issue: str) -> None:
    """
    Trigger remediation action for the given issue.
    Args:
        issue: Type of issue to remediate ('high_cpu' or 'high_disk')
    """
    try:
        response = requests.post(REMEDIATOR_URL, json={"issueType": issue})
        response.raise_for_status()
        send_slack_message(f":tools: Remediation triggered for {issue}: {response.text}")
        logger.info(f"Remediation triggered for {issue}")
    except Exception as e:
        error_msg = f"Failed to trigger remediation: {str(e)}"
        send_slack_message(f":x: {error_msg}")
        logger.error(error_msg)

def main() -> None:
    """Main monitoring loop"""
    logger.info("Starting system monitoring...")
    while True:
        try:
            check_system()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()