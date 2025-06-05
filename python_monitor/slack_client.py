"""
Slack client module for sending messages to Slack channels
"""

import os
import logging
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
DEFAULT_CHANNEL = os.environ.get('SLACK_CHANNEL', '#devops-alerts')

# Initialize Slack client
client = None
if SLACK_BOT_TOKEN:
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        logger.info("Slack client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Slack client: {str(e)}")
        client = None
else:
    logger.warning("SLACK_BOT_TOKEN not found in environment variables")


def send_slack_message(message, channel=None):
    """
    Send a message to a Slack channel.
    
    Args:
        message (str): The message to send
        channel (str, optional): The channel to send to. Defaults to DEFAULT_CHANNEL.
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    if not client:
        error_msg = "Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
        print(f"Slack send error: {error_msg}")
        logger.error(error_msg)
        return False
    
    if not message:
        logger.warning("Attempted to send empty message to Slack")
        return False
    
    target_channel = channel or DEFAULT_CHANNEL
    
    try:
        response = client.chat_postMessage(
            channel=target_channel,
            text=message
        )
        
        if response["ok"]:
            logger.info(f"Message sent successfully to {target_channel}")
            return True
        else:
            error_msg = f"Failed to send message to Slack: {response}"
            print(f"Slack send error: {error_msg}")
            logger.error(error_msg)
            return False
            
    except SlackApiError as e:
        error_msg = f"Slack API error: {e.response['error']}"
        print(f"Slack send error: {error_msg}")
        logger.error(error_msg)
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"Slack send error: {error_msg}")
        logger.error(f"Unexpected error sending Slack message: {error_msg}")
        return False


def test_slack_connection():
    """
    Test the Slack connection by calling auth.test.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    if not client:
        logger.error("Cannot test connection: Slack client not initialized")
        return False
    
    try:
        response = client.auth_test()
        if response["ok"]:
            logger.info(f"Slack connection test successful. Bot: {response.get('user', 'unknown')}")
            return True
        else:
            logger.error(f"Slack connection test failed: {response}")
            return False
    except Exception as e:
        logger.error(f"Slack connection test failed: {str(e)}")
        return False


def get_channel_info(channel):
    """
    Get information about a Slack channel.
    
    Args:
        channel (str): The channel name or ID
        
    Returns:
        dict: Channel information or None if not found
    """
    if not client:
        logger.error("Cannot get channel info: Slack client not initialized")
        return None
    
    try:
        # Remove # from channel name if present for the API call
        channel_id = channel.lstrip('#')
        response = client.conversations_info(channel=channel_id)
        
        if response["ok"]:
            return response["channel"]
        else:
            logger.error(f"Failed to get channel info: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get channel info for {channel}: {str(e)}")
        return None


def send_alert(message, severity="info", channel=None):
    """
    Send an alert message with severity indication.
    
    Args:
        message (str): The alert message
        severity (str): Severity level (info, warning, error, critical)
        channel (str, optional): Channel to send to
    
    Returns:
        bool: True if sent successfully
    """
    # Add emoji based on severity
    emoji_map = {
        "info": "ℹ️",
        "warning": "⚠️", 
        "error": "❌",
        "critical": "🚨"
    }
    
    emoji = emoji_map.get(severity.lower(), "📢")
    formatted_message = f"{emoji} **{severity.upper()}**: {message}"
    
    return send_slack_message(formatted_message, channel)


def send_system_health_report(cpu_usage, memory_usage, disk_usage, channel=None):
    """
    Send a formatted system health report.
    
    Args:
        cpu_usage (float): CPU usage percentage
        memory_usage (float): Memory usage percentage  
        disk_usage (float): Disk usage percentage
        channel (str, optional): Channel to send to
    
    Returns:
        bool: True if sent successfully
    """
    # Determine overall health status
    max_usage = max(cpu_usage, memory_usage, disk_usage)
    if max_usage >= 90:
        status_emoji = "🚨"
        status = "CRITICAL"
    elif max_usage >= 80:
        status_emoji = "⚠️"
        status = "WARNING"
    else:
        status_emoji = "✅"
        status = "HEALTHY"
    
    message = f"""
{status_emoji} **System Health Report - {status}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️  **CPU Usage:** {cpu_usage:.1f}%
🧠 **Memory Usage:** {memory_usage:.1f}%
💾 **Disk Usage:** {disk_usage:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return send_slack_message(message.strip(), channel)


# Test the connection when module is imported (if configured)
if client and SLACK_BOT_TOKEN:
    try:
        if test_slack_connection():
            logger.info("✅ Slack integration ready")
        else:
            logger.warning("⚠️ Slack connection test failed on startup")
    except Exception as e:
        logger.error(f"Error testing Slack connection on startup: {str(e)}")
else:
    logger.info("Slack client not configured - set SLACK_BOT_TOKEN to enable")