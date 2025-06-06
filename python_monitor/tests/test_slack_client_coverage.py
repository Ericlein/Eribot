"""
Additional tests for clients/slack.py to improve coverage from 60%
Targets specific uncovered lines: 10, 50-51, 57, 63-71, 105-123, 126, 129, 132, 135-140
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from slack_sdk.errors import SlackApiError

from clients.slack import (
    SlackClient,
    SlackError,
    AuthenticationError,
    RateLimitError
)
from config.models import SlackConfig


class TestSlackClientCoverageBoost:
    """Additional tests to hit uncovered lines in slack client"""

    @pytest.fixture
    def slack_config(self):
        """Provide Slack configuration for tests"""
        return SlackConfig(
            channel="#test-alerts",
            token="xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx",
            username="TestBot",
            icon_emoji=":robot_face:"
        )

    @pytest.mark.unit
    def test_get_logger_function_call(self):
        """Test the get_logger function at module level (line 10)"""
        from clients.slack import get_logger
        
        logger = get_logger("test_slack")
        assert logger.name == "test_slack"

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_slack_client_config_attribute_access(self, mock_webclient_class, slack_config):
        """Test accessing config attributes (lines 50-51)"""
        # Mock successful WebClient
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        client = SlackClient(slack_config)
        
        # Access config attributes (lines 50-51)
        assert client.config.token == slack_config.token
        assert client.config.channel == slack_config.channel
        assert client.config.username == slack_config.username
        assert client.config.icon_emoji == slack_config.icon_emoji

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_auth_test_response_data_access(self, mock_webclient_class, slack_config):
        """Test accessing auth test response data (lines 57, 63-71)"""
        # Mock WebClient with detailed auth response
        mock_client_instance = MagicMock()
        mock_auth_response = {
            "ok": True,
            "user": "test_bot_user",
            "team": "test_team_name"
        }
        mock_client_instance.auth_test.return_value = mock_auth_response
        mock_webclient_class.return_value = mock_client_instance
        
        # Create client - this will call _test_connection internally
        client = SlackClient(slack_config)
        
        # Verify the client was created successfully
        assert client is not None
        assert client.config == slack_config

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_slack_api_error_handling_in_test_connection(self, mock_webclient_class, slack_config):
        """Test SlackApiError handling in _test_connection (lines 63-71)"""
        mock_client_instance = MagicMock()
        mock_webclient_class.return_value = mock_client_instance
        
        # Test invalid_auth error - this should be caught during client creation
        error_response = {"error": "invalid_auth"}
        slack_error = SlackApiError("Auth failed", error_response)
        slack_error.response = error_response  # Ensure response attribute is set
        mock_client_instance.auth_test.side_effect = slack_error
        
        # The SlackClient catches SlackApiError and re-raises as SlackError
        with pytest.raises(SlackError):
            SlackClient(slack_config)

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_slack_api_error_rate_limited_in_send_message(self, mock_webclient_class, slack_config):
        """Test rate_limited error in send_message (lines 126)"""
        # Mock successful client creation first
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Create client successfully
        client = SlackClient(slack_config)
        
        # Now mock rate limit error in send_message
        error_response = {"error": "rate_limited", "retry_after": 60}
        slack_error = SlackApiError("Rate limited", error_response)
        slack_error.response = error_response
        mock_client_instance.chat_postMessage.side_effect = slack_error
        
        with pytest.raises(RateLimitError):
            client.send_message("Test message")

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_slack_api_error_invalid_auth_in_send_message(self, mock_webclient_class, slack_config):
        """Test invalid_auth error in send_message (lines 132)"""
        # Mock successful client creation first
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Create client successfully
        client = SlackClient(slack_config)
        
        # Now mock invalid auth error in send_message
        error_response = {"error": "invalid_auth"}
        slack_error = SlackApiError("Invalid auth", error_response)
        slack_error.response = error_response
        mock_client_instance.chat_postMessage.side_effect = slack_error
        
        with pytest.raises(AuthenticationError):
            client.send_message("Test message")

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_slack_api_error_other_error_in_test_connection(self, mock_webclient_class, slack_config):
        """Test other SlackApiError in _test_connection (lines 70-71)"""
        mock_client_instance = MagicMock()
        mock_webclient_class.return_value = mock_client_instance
        
        # Test other error
        error_response = {"error": "some_other_error"}
        mock_client_instance.auth_test.side_effect = SlackApiError("Other error", error_response)
        
        with pytest.raises(SlackError):
            SlackClient(slack_config)

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_emoji_mapping(self, mock_webclient_class, slack_config):
        """Test emoji mapping in send_message (lines 105-123)"""
        # Mock successful client
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        client = SlackClient(slack_config)
        
        # Test different severity levels to hit emoji mapping (lines 105-123)
        severities = ['info', 'warning', 'error', 'critical', 'success', 'unknown']
        
        for severity in severities:
            result = client.send_message("Test message", severity=severity)
            assert result is True
        
        # Verify chat_postMessage was called for each severity
        assert mock_client_instance.chat_postMessage.call_count == len(severities)

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_rate_limit_error(self, mock_webclient_class, slack_config):
        """Test rate limit error in send_message (lines 126) - duplicate removed"""
        pass  # This test is now covered by test_slack_api_error_rate_limited_in_send_message

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_channel_not_found_error(self, mock_webclient_class, slack_config):
        """Test channel_not_found error in send_message (lines 129)"""
        # Mock successful client creation
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Mock channel not found error
        error_response = {"error": "channel_not_found"}
        mock_client_instance.chat_postMessage.side_effect = SlackApiError("Channel not found", error_response)
        
        client = SlackClient(slack_config)
        
        with pytest.raises(SlackError, match="Channel not found"):
            client.send_message("Test message")

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_invalid_auth_error(self, mock_webclient_class, slack_config):
        """Test invalid_auth error in send_message (lines 132) - duplicate removed"""
        pass  # This test is now covered by test_slack_api_error_invalid_auth_in_send_message

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_other_slack_error(self, mock_webclient_class, slack_config):
        """Test other SlackApiError in send_message (lines 135)"""
        # Mock successful client creation
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Mock other slack error
        error_response = {"error": "some_other_slack_error"}
        mock_client_instance.chat_postMessage.side_effect = SlackApiError("Other error", error_response)
        
        client = SlackClient(slack_config)
        
        with pytest.raises(SlackError):
            client.send_message("Test message")

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_unexpected_exception(self, mock_webclient_class, slack_config):
        """Test unexpected exception in send_message (lines 139-140)"""
        # Mock successful client creation
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Mock unexpected exception
        mock_client_instance.chat_postMessage.side_effect = Exception("Unexpected error")
        
        client = SlackClient(slack_config)
        
        with pytest.raises(SlackError, match="Unexpected error sending message"):
            client.send_message("Test message")

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_helper_methods(self, mock_webclient_class, slack_config):
        """Test the helper methods (send_alert, send_success_message, send_error_message)"""
        # Mock successful client
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        client = SlackClient(slack_config)
        
        # Test helper methods
        assert client.send_alert("Alert message") is True
        assert client.send_success_message("Success message") is True
        assert client.send_error_message("Error message") is True

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_test_connection_method_standalone(self, mock_webclient_class, slack_config):
        """Test the standalone test_connection method"""
        # Mock successful client
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        client = SlackClient(slack_config)
        
        # Test successful connection
        result = client.test_connection()
        assert result is True
        
        # Test failed connection
        mock_client_instance.auth_test.side_effect = Exception("Connection failed")
        result = client.test_connection()
        assert result is False

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_with_custom_channel(self, mock_webclient_class, slack_config):
        """Test send_message with custom channel parameter"""
        # Mock successful client
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        client = SlackClient(slack_config)
        
        # Test with custom channel
        result = client.send_message("Test message", channel="#custom-channel")
        assert result is True
        
        # Verify the custom channel was used
        call_args = mock_client_instance.chat_postMessage.call_args
        assert call_args[1]['channel'] == "#custom-channel"

    @pytest.mark.unit
    @patch('clients.slack.WebClient')
    def test_send_message_response_not_ok(self, mock_webclient_class, slack_config):
        """Test send_message when response is not ok"""
        # Mock successful client creation
        mock_client_instance = MagicMock()
        mock_client_instance.auth_test.return_value = {"ok": True, "user": "test", "team": "test"}
        mock_webclient_class.return_value = mock_client_instance
        
        # Mock response that's not ok
        mock_client_instance.chat_postMessage.return_value = {"ok": False, "error": "some_error"}
        
        client = SlackClient(slack_config)
        result = client.send_message("Test message")
        
        assert result is False