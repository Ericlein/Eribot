import psutil
import time
from slack_client import send_slack_message
import requests

REMEDIATOR_URL = "http://localhost:5001/remediate"

def check_system():
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/').percent

    if cpu > 85:
        send_slack_message(f":warning: High CPU usage detected: {cpu}%")
        trigger_remediation("high_cpu")

    if disk > 90:
        send_slack_message(f":warning: High Disk usage: {disk}%")
        trigger_remediation("high_disk")

def trigger_remediation(issue):
    try:
        response = requests.post(REMEDIATOR_URL, json={"issue": issue})
        send_slack_message(f":tools: Remediation triggered for {issue}: {response.text}")
    except Exception as e:
        send_slack_message(f":x: Failed to trigger remediation: {str(e)}")

if __name__ == "__main__":
    while True:
        check_system()
        time.sleep(60)
