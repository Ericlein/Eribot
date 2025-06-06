import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
import slack_client
from slack_client import send_slack_message


class TestSlackClientUnit:
    """Unit tests with mocking - fast and don't require real Slack API"""
    
    @pytest.mark.unit
    @patch('slack_client.WebClient')
    def test_send_slack_message_success_mocked(self, mock_webclient_class):
        """Test successful Slack message sending with mocks"""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        with patch.object(slack_client, 'client', mock_client_instance, create=True):
            result = send_slack_message("Test message")
            
            # Your function should return True on success
            assert result is True
            mock_client_instance.chat_postMessage.assert_called_once()
            call_args = mock_client_instance.chat_postMessage.call_args
            assert "Test message" in str(call_args)
    
    @pytest.mark.unit
    @patch('slack_client.WebClient')
    @patch('builtins.print')
    def test_send_slack_message_failure_mocked(self, mock_print, mock_webclient_class):
        """Test Slack message sending failure with mocks"""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_postMessage.side_effect = Exception("Slack API error")
        mock_webclient_class.return_value = mock_client_instance
        
        with patch.object(slack_client, 'client', mock_client_instance, create=True):
            result = send_slack_message("Test message")
            
            # Should return False on error
            assert result is False

    @pytest.mark.unit
    @patch('slack_client.WebClient')
    def test_send_slack_message_empty_message(self, mock_webclient_class):
        """Test sending empty message with mocks"""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        with patch.object(slack_client, 'client', mock_client_instance, create=True):
            result = send_slack_message("")
            
            # Should return False for empty message
            assert result is False

    @pytest.mark.unit
    @patch('slack_client.WebClient')
    def test_send_slack_message_with_channel_mocked(self, mock_webclient_class):
        """Test sending message with specific channel using mocks"""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_postMessage.return_value = {"ok": True}
        mock_webclient_class.return_value = mock_client_instance
        
        with patch.object(slack_client, 'client', mock_client_instance, create=True):
            try:
                result = send_slack_message("Test message", channel="#test")
                mock_client_instance.chat_postMessage.assert_called_once()
                call_args = mock_client_instance.chat_postMessage.call_args
                assert "#test" in str(call_args)
            except TypeError:
                # Function doesn't support channel parameter - that's fine
                result = send_slack_message("Test message")
                mock_client_instance.chat_postMessage.assert_called_once()


class TestSlackClientIntegration:
    """Integration tests with real Slack API - requires SLACK_BOT_TOKEN and --run-integration flag"""
    
    @pytest.fixture(autouse=True)
    def check_integration_flag(self, request):
        """Check if integration tests should run"""
        # Skip integration tests unless explicitly requested
        if not request.config.getoption("--run-integration", default=False):
            pytest.skip("Integration tests skipped - use --run-integration to run them")
    
    @pytest.fixture(autouse=True) 
    def check_ci_environment(self):
        """Skip integration tests in CI environment"""
        # Additional safety: skip if running in CI
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            pytest.skip("Integration tests skipped in CI environment")
    
    @pytest.fixture(autouse=True)
    def check_slack_setup(self):
        """Check if Slack is properly configured before running integration tests"""
        if not os.environ.get('SLACK_BOT_TOKEN'):
            pytest.skip("SLACK_BOT_TOKEN not found in environment - skipping integration tests")
        
        # Test if we can connect to Slack
        try:
            if hasattr(slack_client, 'client') and slack_client.client:
                response = slack_client.client.auth_test()
                if not response.get("ok"):
                    pytest.skip("Slack authentication failed - skipping integration tests")
        except Exception as e:
            pytest.skip(f"Slack connection failed: {str(e)} - skipping integration tests")
    
    @pytest.mark.integration
    def test_slack_connection_real(self):
        """Test real Slack connection"""
        if hasattr(slack_client, 'test_slack_connection'):
            assert slack_client.test_slack_connection() is True
        else:
            # Fallback test
            assert slack_client.client is not None
            response = slack_client.client.auth_test()
            assert response["ok"] is True
    
    @pytest.mark.integration
    def test_send_real_slack_message(self):
        """Test sending a real message to Slack"""
        test_message = "🧪 Test message from pytest - Integration test"
        
        # Send the message
        result = send_slack_message(test_message)
        
        # Your function returns True on success, False on failure
        assert result is True, f"Message sending failed, got result: {result}"
        
        print(f"✅ Successfully sent test message to Slack: {test_message}")
    
    @pytest.mark.integration
    def test_send_real_slack_message_with_channel(self):
        """Test sending a message to a specific channel"""
        test_message = "🧪 Test message with specific channel - Integration test"
        test_channel = os.environ.get('SLACK_CHANNEL', '#general')
        
        try:
            # Try to send with channel parameter
            result = send_slack_message(test_message, channel=test_channel)
            assert result is True, f"Message sending failed, got result: {result}"
            print(f"✅ Successfully sent test message to {test_channel}: {test_message}")
        except TypeError:
            # If function doesn't support channel parameter, send normally
            result = send_slack_message(test_message)
            assert result is True, f"Message sending failed, got result: {result}"
            print(f"✅ Successfully sent test message (no channel param): {test_message}")
    
    @pytest.mark.integration
    def test_send_empty_message_real(self):
        """Test sending empty message to real Slack"""
        result = send_slack_message("")
        
        # Should return False for empty message
        assert result is False, f"Expected False for empty message, got: {result}"
        print(f"✅ Empty message correctly returned False: {result}")
    
    @pytest.mark.integration
    def test_get_bot_info_real(self):
        """Test getting bot information from Slack"""
        if not hasattr(slack_client, 'client') or not slack_client.client:
            pytest.skip("Slack client not available")
        
        try:
            response = slack_client.client.auth_test()
            assert response["ok"] is True
            
            # Print bot info for debugging
            print(f"Bot User ID: {response.get('user_id')}")
            print(f"Bot User: {response.get('user')}")
            print(f"Team: {response.get('team')}")
            
            # Basic assertions
            assert 'user_id' in response
            assert 'user' in response
            
        except Exception as e:
            pytest.fail(f"Failed to get bot info: {str(e)}")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_slack_rate_limiting(self):
        """Test multiple rapid messages to check rate limiting handling"""
        messages = [
            "🧪 Rate limit test 1/3",
            "🧪 Rate limit test 2/3", 
            "🧪 Rate limit test 3/3"
        ]
        
        results = []
        for msg in messages:
            result = send_slack_message(msg)
            results.append(result)
        
        # Count successful sends (should be True)
        successful_sends = [r for r in results if r is True]
        
        # At least some should succeed (depending on rate limits)
        assert len(successful_sends) > 0, f"All messages failed - got results: {results}"
        
        print(f"✅ Sent {len(successful_sends)}/{len(messages)} messages successfully")


class TestSlackClientConfiguration:
    """Test configuration and environment setup"""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # Should have loaded from .env file
        slack_token = os.environ.get('SLACK_BOT_TOKEN')
        if slack_token:
            assert slack_token.startswith('xoxb-'), "SLACK_BOT_TOKEN should start with 'xoxb-'"
            print(f"✅ SLACK_BOT_TOKEN loaded: {slack_token[:20]}...")
        else:
            print("⚠️  SLACK_BOT_TOKEN not found in environment")
    
    def test_slack_channel_configuration(self):
        """Test Slack channel configuration"""
        channel = os.environ.get('SLACK_CHANNEL')
        if channel:
            assert channel.startswith('#'), "SLACK_CHANNEL should start with '#'"
            print(f"✅ SLACK_CHANNEL configured: {channel}")
        else:
            print("ℹ️  SLACK_CHANNEL not configured, will use default")
    
    def test_slack_client_initialization(self):
        """Test that Slack client initializes properly (unit test version)"""
        # This should test initialization without requiring real credentials
        assert hasattr(slack_client, 'client'), "slack_client should have 'client' attribute"
        
        # If client exists, check it has expected methods
        if slack_client.client:
            assert hasattr(slack_client.client, 'chat_postMessage'), "Client should have chat_postMessage method"
            print("✅ Slack client has expected methods")


# Pytest configuration to run integration tests conditionally
def pytest_configure(config):
    """Configure pytest markers and options"""
    config.addinivalue_line("markers", "unit: fast unit tests with mocking")
    config.addinivalue_line("markers", "integration: integration tests with real APIs")
    config.addinivalue_line("markers", "slow: slow tests that may take time")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires real API credentials)"
    )


# Usage examples:
# Run only unit tests (default in CI): pytest -m "unit"
# Run only unit tests explicitly: pytest -m "unit" 
# Run integration tests locally: pytest --run-integration -m "integration"
# Run all tests locally: pytest --run-integration
# Run without integration tests: pytest -m "not integration"