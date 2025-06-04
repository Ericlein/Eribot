from slack_sdk import WebClient
import os

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL = "#devops-alerts"

client = WebClient(token=SLACK_TOKEN)

def send_slack_message(text):
    try:
        client.chat_postMessage(channel=CHANNEL, text=text)
    except Exception as e:
        print(f"Slack send error: {e}")
