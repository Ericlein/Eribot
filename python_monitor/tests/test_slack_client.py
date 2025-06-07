"""
Tests for Slack client module
"""

import pytest
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv

load_dotenv()


class TestSlackClientUnit:
    """Unit tests with mocking - fast and don't require real Slack API"""

    @pytest.mark.unit
    @patch("clients.slack.WebClient")
    def test_slack_client_creation(self, mock_webclient_class, slack_config):
        """Test SlackClient creation"""
        from clients.slack import SlackClient

        # Mock the WebClient and its methods
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {
            "ok": True,
            "user": "test",
            "team": "test",
        }
        mock_webclient_class.return_value = mock_client_instance

        client = SlackClient(slack_config)
        assert client.config == slack_config

        # Verify WebClient was called with the token
        mock_webclient_class.assert_called_once_with(token=slack_config.token)
        mock_client_instance.auth_test.assert_called_once()

    @pytest.mark.unit
    @patch("clients.slack.WebClient")
    def test_send_slack_message_success(self, mock_webclient_class, slack_config):
        """Test successful Slack message sending with mocks"""
        from clients.slack import SlackClient

        # Mock the WebClient and its methods
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {
            "ok": True,
            "user": "test",
            "team": "test",
        }
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance

        client = SlackClient(slack_config)
        result = client.send_message("Test message")

        assert result is True
        mock_client_instance.chat_postMessage.assert_called_once()

        # Check that the message was formatted correctly
        call_args = mock_client_instance.chat_postMessage.call_args
        assert "Test message" in str(call_args)

    @pytest.mark.unit
    @patch("clients.slack.WebClient")
    def test_send_empty_message(self, mock_webclient_class, slack_config):
        """Test sending empty message"""
        from clients.slack import SlackClient

        # Mock the WebClient
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {
            "ok": True,
            "user": "test",
            "team": "test",
        }
        mock_webclient_class.return_value = mock_client_instance

        client = SlackClient(slack_config)
        result = client.send_message("")

        # Should return False for empty message
        assert result is False
        # Should not call chat_postMessage for empty message
        mock_client_instance.chat_postMessage.assert_not_called()

    @pytest.mark.unit
    @patch("clients.slack.WebClient")
    def test_slack_client_invalid_token_format(self, mock_webclient_class):
        """Test SlackClient with invalid token format"""
        from clients.slack import SlackClient, AuthenticationError
        from config.models import SlackConfig

        # Test with invalid token format
        invalid_config = SlackConfig(
            channel="#test",
            token="invalid-token-format",  # Doesn't start with xoxb-
            username="TestBot",
        )

        with pytest.raises(AuthenticationError, match="Invalid Slack token format"):
            SlackClient(invalid_config)

    @pytest.mark.unit
    @patch("clients.slack.WebClient")
    def test_slack_client_empty_token(self, mock_webclient_class):
        """Test SlackClient with empty token"""
        from clients.slack import SlackClient, AuthenticationError
        from config.models import SlackConfig

        # Test with empty token
        invalid_config = SlackConfig(
            channel="#test", token="", username="TestBot"
        )  # Empty token

        with pytest.raises(AuthenticationError, match="SLACK_BOT_TOKEN is required"):
            SlackClient(invalid_config)


class TestSlackClientIntegration:
    """Integration tests with real Slack API - requires token and --run-integration flag"""

    @pytest.fixture(autouse=True)
    def check_integration_flag(self, request):
        """Check if integration tests should run"""
        if not request.config.getoption("--run-integration", default=False):
            pytest.skip("Integration tests skipped - use --run-integration to run them")

    @pytest.fixture(autouse=True)
    def check_ci_environment(self):
        """Skip integration tests in CI environment"""
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            pytest.skip("Integration tests skipped in CI environment")

    @pytest.fixture(autouse=True)
    def check_slack_setup(self):
        """Check if Slack is properly configured"""
        if not os.environ.get("SLACK_BOT_TOKEN"):
            pytest.skip("SLACK_BOT_TOKEN not found - skipping integration tests")

    @pytest.mark.integration
    def test_real_slack_message(self, slack_config):
        """Test sending a real message to Slack"""
        from clients.slack import SlackClient

        # Use real token from environment
        slack_config.token = os.environ.get("SLACK_BOT_TOKEN", "")

        client = SlackClient(slack_config)
        result = client.send_message(" Test message from pytest - Integration test")

        assert result is True
