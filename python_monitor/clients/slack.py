import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports during transition
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config.models import SlackConfig


def get_logger(name):
    return logging.getLogger(name)


class SlackError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class RateLimitError(Exception):
    pass


class SlackClient:
    def __init__(self, config: SlackConfig):
        self.config = config
        self.logger = get_logger("slack_client")

        if not config.token:
            raise AuthenticationError("SLACK_BOT_TOKEN is required")

        if not config.token.startswith("xoxb-"):
            raise AuthenticationError(
                "Invalid Slack token format. Expected bot token starting with xoxb-"
            )

        try:
            self.client = WebClient(token=config.token)
            self._test_connection()
            self.logger.info(" Slack client initialized successfully")
        except Exception as e:
            raise SlackError(f"Failed to initialize Slack client: {str(e)}")

    def _test_connection(self) -> None:
        try:
            response = self.client.auth_test()
            if not response.get("ok"):
                raise AuthenticationError("Slack authentication failed")

            user = response.get("user", "unknown")
            team = response.get("team", "unknown")
            self.logger.info(f"Authenticated as {user} on team {team}")

        except SlackApiError as e:
            error_code = e.response.get("error", "unknown")
            if error_code == "invalid_auth":
                raise AuthenticationError("Invalid Slack token")
            elif error_code == "rate_limited":
                retry_after = e.response.get("retry_after", 60)
                raise RateLimitError("slack", retry_after)
            else:
                raise SlackError(f"Slack API error during auth test: {error_code}")

    def send_message(
        self, message: str, channel: Optional[str] = None, severity: str = "info"
    ) -> bool:
        if not message or not message.strip():
            self.logger.warning("Attempted to send empty message")
            return False

        target_channel = channel or self.config.channel

        emoji_map = {
            "info": "ℹ",
            "warning": "",
            "error": "",
            "critical": "",
            "success": "",
        }

        emoji = emoji_map.get(severity.lower(), "")
        formatted_message = f"{emoji} {message}"

        try:
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=formatted_message,
                username=self.config.username,
                icon_emoji=self.config.icon_emoji,
            )

            if response.get("ok"):
                self.logger.debug(f"Message sent to {target_channel}: {message[:50]}...")
                return True
            else:
                error_msg = f"Failed to send message: {response}"
                self.logger.error(error_msg)
                return False

        except SlackApiError as e:
            error_code = e.response.get("error", "unknown")

            if error_code == "rate_limited":
                retry_after = e.response.get("retry_after", 60)
                raise RateLimitError("slack", retry_after)
            elif error_code == "channel_not_found":
                raise SlackError(f"Channel not found: {target_channel}")
            elif error_code == "invalid_auth":
                raise AuthenticationError("Invalid Slack token")
            else:
                raise SlackError(f"Slack API error: {error_code}")

        except Exception as e:
            raise SlackError(f"Unexpected error sending message: {str(e)}")

    def send_alert(self, message: str, severity: str = "warning") -> bool:
        return self.send_message(message, severity=severity)

    def send_success_message(self, message: str) -> bool:
        return self.send_message(message, severity="success")

    def send_error_message(self, message: str) -> bool:
        return self.send_message(message, severity="error")

    def test_connection(self) -> bool:
        try:
            response = self.client.auth_test()
            return response.get("ok", False)
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
