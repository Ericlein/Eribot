"""
Slack client for EriBot notifications.

Refactored from slack_client.py with better error handling and structure.
"""

import logging
from typing import Optional, Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from python_monitor.config.models import SlackConfig
from python_monitor.utils.logger import get_logger
from python_monitor.utils.exceptions import SlackError, AuthenticationError, RateLimitError


class SlackClient:
    """Enhanced Slack client with better error handling and messaging capabilities."""
    
    def __init__(self, config: SlackConfig):
        """
        Initialize Slack client.
        
        Args:
            config: Slack configuration
            
        Raises:
            AuthenticationError: If token is invalid
            SlackError: If client initialization fails
        """
        self.config = config
        self.logger = get_logger("slack_client")
        
        if not config.token:
            raise AuthenticationError("SLACK_BOT_TOKEN is required")
        
        if not config.token.startswith('xoxb-'):
            raise AuthenticationError("Invalid Slack token format. Expected bot token starting with 'xoxb-'")
        
        try:
            self.client = WebClient(token=config.token)
            self._test_connection()
            self.logger.info("✅ Slack client initialized successfully")
        except Exception as e:
            raise SlackError(f"Failed to initialize Slack client: {str(e)}")
    
    def _test_connection(self) -> None:
        """Test Slack connection during initialization."""
        try:
            response = self.client.auth_test()
            if not response.get("ok"):
                raise AuthenticationError("Slack authentication failed")
            
            user = response.get('user', 'unknown')
            team = response.get('team', 'unknown')
            self.logger.info(f"Authenticated as {user} on team {team}")
            
        except SlackApiError as e:
            error_code = e.response.get('error', 'unknown')
            if error_code == 'invalid_auth':
                raise AuthenticationError("Invalid Slack token")
            elif error_code == 'rate_limited':
                retry_after = e.response.get('retry_after', 60)
                raise RateLimitError("slack", retry_after)
            else:
                raise SlackError(f"Slack API error during auth test: {error_code}")
    
    def send_message(
        self, 
        message: str, 
        channel: Optional[str] = None,
        severity: str = "info"
    ) -> bool:
        """
        Send a message to Slack.
        
        Args:
            message: The message to send
            channel: Channel to send to (defaults to config channel)
            severity: Message severity (info, warning, error, critical)
            
        Returns:
            True if message was sent successfully
            
        Raises:
            SlackError: If message sending fails
        """
        if not message or not message.strip():
            self.logger.warning("Attempted to send empty message")
            return False
        
        target_channel = channel or self.config.channel
        
        # Add emoji based on severity
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️", 
            "error": "❌",
            "critical": "🚨",
            "success": "✅"
        }
        
        emoji = emoji_map.get(severity.lower(), "📢")
        formatted_message = f"{emoji} {message}"
        
        try:
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=formatted_message,
                username=self.config.username,
                icon_emoji=self.config.icon_emoji
            )
            
            if response.get("ok"):
                self.logger.debug(f"Message sent to {target_channel}: {message[:50]}...")
                return True
            else:
                error_msg = f"Failed to send message: {response}"
                self.logger.error(error_msg)
                return False
                
        except SlackApiError as e:
            error_code = e.response.get('error', 'unknown')
            
            if error_code == 'rate_limited':
                retry_after = e.response.get('retry_after', 60)
                raise RateLimitError("slack", retry_after)
            elif error_code == 'channel_not_found':
                raise SlackError(f"Channel not found: {target_channel}")
            elif error_code == 'invalid_auth':
                raise AuthenticationError("Invalid Slack token")
            else:
                raise SlackError(f"Slack API error: {error_code}")
                
        except Exception as e:
            raise SlackError(f"Unexpected error sending message: {str(e)}")
    
    def send_alert(self, message: str, severity: str = "warning") -> bool:
        """Send an alert message with appropriate formatting."""
        return self.send_message(message, severity=severity)
    
    def send_success_message(self, message: str) -> bool:
        """Send a success message."""
        return self.send_message(message, severity="success")
    
    def send_error_message(self, message: str) -> bool:
        """Send an error message."""
        return self.send_message(message, severity="error")
    
    def send_critical_alert(self, message: str) -> bool:
        """Send a critical alert."""
        return self.send_message(message, severity="critical")
    
    def send_system_health_report(
        self, 
        cpu_usage: float, 
        memory_usage: float, 
        disk_usage: float
    ) -> bool:
        """
        Send a formatted system health report.
        
        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage percentage  
            disk_usage: Disk usage percentage
            
        Returns:
            True if sent successfully
        """
        # Determine overall health status
        max_usage = max(cpu_usage, memory_usage, disk_usage)
        if max_usage >= 90:
            severity = "critical"
            status = "CRITICAL"
        elif max_usage >= 80:
            severity = "warning"
            status = "WARNING"
        else:
            severity = "info"
            status = "HEALTHY"
        
        message = f"""**System Health Report - {status}**
🖥️  **CPU Usage:** {cpu_usage:.1f}%
🧠 **Memory Usage:** {memory_usage:.1f}%
💾 **Disk Usage:** {disk_usage:.1f}%"""
        
        return self.send_message(message, severity=severity)
    
    def send_remediation_update(
        self, 
        issue_type: str, 
        result_message: str, 
        success: bool
    ) -> bool:
        """
        Send a remediation update message.
        
        Args:
            issue_type: Type of issue being remediated
            result_message: Result message from remediation
            success: Whether remediation was successful
            
        Returns:
            True if sent successfully
        """
        if success:
            message = f"🛠️ **Remediation Successful**\n**Issue:** {issue_type}\n**Result:** {result_message}"
            severity = "success"
        else:
            message = f"❌ **Remediation Failed**\n**Issue:** {issue_type}\n**Error:** {result_message}"
            severity = "error"
        
        return self.send_message(message, severity=severity)
    
    def test_connection(self) -> bool:
        """
        Test the Slack connection.
        
        Returns:
            True if connection is working
        """
        try:
            response = self.client.auth_test()
            return response.get("ok", False)
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False