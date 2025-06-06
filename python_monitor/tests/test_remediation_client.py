"""
Comprehensive tests for remediation client module
This should bring the coverage up to 80%+
"""

import pytest
import requests
from unittest.mock import Mock, patch

# Import the classes we're testing
from clients.remediation import (
    RemediationClient,
    RemediationError,
    NetworkError,
    ServiceUnavailableError,
    EriTimeoutError,
)
from config.models import RemediatorConfig


class TestRemediationClientUnit:
    """Unit tests for RemediationClient with comprehensive mocking"""

    @pytest.fixture
    def remediation_config(self):
        """Create a test remediation configuration"""
        return RemediatorConfig(
            url="http://localhost:5001", timeout=30, retry_attempts=3
        )

    @pytest.fixture
    def mock_requests_session(self):
        """Mock requests session"""
        with patch("clients.remediation.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            yield mock_session

    @pytest.mark.unit
    def test_remediation_client_creation_success(
        self, mock_requests_session, remediation_config
    ):
        """Test successful RemediationClient creation"""
        # Mock successful health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.get.return_value = mock_response

        client = RemediationClient(remediation_config)

        assert client.config == remediation_config
        assert hasattr(client, "session")
        assert hasattr(client, "logger")

        # Verify session configuration
        mock_requests_session.mount.assert_called()
        assert mock_requests_session.timeout == remediation_config.timeout

    @pytest.mark.unit
    def test_remediation_client_creation_health_check_failure(
        self, mock_requests_session, remediation_config
    ):
        """Test RemediationClient creation when health check fails"""
        # Mock failed health check
        mock_response = Mock()
        mock_response.status_code = 503
        mock_requests_session.get.return_value = mock_response

        # Should still create client but log warning
        client = RemediationClient(remediation_config)
        assert client.config == remediation_config

    @pytest.mark.unit
    def test_remediation_client_creation_health_check_exception(
        self, mock_requests_session, remediation_config
    ):
        """Test RemediationClient creation when health check raises exception"""
        # Mock health check exception
        mock_requests_session.get.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        # Should still create client but log warning
        client = RemediationClient(remediation_config)
        assert client.config == remediation_config

    @pytest.mark.unit
    def test_test_connection_success(self, mock_requests_session, remediation_config):
        """Test successful connection test"""
        # Mock successful health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.get.return_value = mock_response

        client = RemediationClient(remediation_config)
        result = client._test_connection()

        assert result is True
        mock_requests_session.get.assert_called_with(
            f"{remediation_config.url}/health", timeout=5
        )

    @pytest.mark.unit
    def test_test_connection_failure(self, mock_requests_session, remediation_config):
        """Test failed connection test"""
        # Mock failed health check
        mock_response = Mock()
        mock_response.status_code = 503
        mock_requests_session.get.return_value = mock_response

        client = RemediationClient(remediation_config)
        result = client._test_connection()

        assert result is False

    @pytest.mark.unit
    def test_test_connection_exception(self, mock_requests_session, remediation_config):
        """Test connection test with exception"""
        # Mock health check exception
        mock_requests_session.get.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        client = RemediationClient(remediation_config)
        result = client._test_connection()

        assert result is False

    @pytest.mark.unit
    def test_trigger_remediation_success_new_api(
        self, mock_requests_session, remediation_config
    ):
        """Test successful remediation trigger using new API endpoint"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful remediation response
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.return_value = {
            "success": True,
            "message": "Remediation completed successfully",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_cpu", {"cpu_percent": 95.0})

        assert result is True

        # Verify the correct endpoint was called
        expected_url = f"{remediation_config.url}/api/remediation/execute"
        mock_requests_session.post.assert_called_with(
            expected_url,
            json={
                "issueType": "high_cpu",
                "context": {"cpu_percent": 95.0},
                "timestamp": None,
                "hostname": None,
            },
            headers={"Content-Type": "application/json"},
            timeout=remediation_config.timeout,
        )

    @pytest.mark.unit
    def test_trigger_remediation_success_legacy_api(
        self, mock_requests_session, remediation_config
    ):
        """Test successful remediation trigger falling back to legacy API"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock 404 for new API, success for legacy
        mock_404_response = Mock()
        mock_404_response.status_code = 404
        mock_404_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_404_response
        )

        mock_legacy_response = Mock()
        mock_legacy_response.status_code = 200
        mock_legacy_response.json.return_value = {
            "success": True,
            "message": "Legacy remediation completed",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = [
            requests.exceptions.HTTPError(response=mock_404_response),  # New API fails
            mock_legacy_response,  # Legacy API succeeds
        ]

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_disk")

        assert result is True

        # Verify both endpoints were tried
        assert mock_requests_session.post.call_count == 2

    @pytest.mark.unit
    def test_trigger_remediation_success_non_json_response(
        self, mock_requests_session, remediation_config
    ):
        """Test successful remediation with non-JSON response"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful remediation response (non-JSON)
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.side_effect = ValueError("Not JSON")
        mock_remediation_response.text = "Remediation completed"

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_memory")

        assert result is True

    @pytest.mark.unit
    def test_trigger_remediation_failure_response(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with failure response"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock failed remediation response
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.return_value = {
            "success": False,
            "message": "Remediation failed: Invalid parameters",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)

        with pytest.raises(
            RemediationError, match="Remediation failed: Invalid parameters"
        ):
            client.trigger_remediation("invalid_type")

    @pytest.mark.unit
    def test_trigger_remediation_timeout(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with timeout"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = requests.exceptions.Timeout(
            "Request timed out"
        )

        client = RemediationClient(remediation_config)

        with pytest.raises(EriTimeoutError):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_connection_error(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with connection error"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        client = RemediationClient(remediation_config)

        with pytest.raises(
            ServiceUnavailableError, match="Could not connect to remediation service"
        ):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_http_error_400(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with HTTP 400 error"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_error_response = Mock()
        mock_error_response.status_code = 400

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = requests.exceptions.HTTPError(
            response=mock_error_response
        )

        client = RemediationClient(remediation_config)

        with pytest.raises(RemediationError, match="Invalid remediation request"):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_http_error_404(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with HTTP 404 error on both endpoints"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_error_response = Mock()
        mock_error_response.status_code = 404

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = requests.exceptions.HTTPError(
            response=mock_error_response
        )

        client = RemediationClient(remediation_config)

        with pytest.raises(RemediationError, match="Unknown issue type"):
            client.trigger_remediation("unknown_type")

    @pytest.mark.unit
    def test_trigger_remediation_http_error_503(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with HTTP 503 error"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_error_response = Mock()
        mock_error_response.status_code = 503

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = requests.exceptions.HTTPError(
            response=mock_error_response
        )

        client = RemediationClient(remediation_config)

        with pytest.raises(
            ServiceUnavailableError, match="Remediation service temporarily unavailable"
        ):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_unexpected_exception(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with unexpected exception"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = Exception("Unexpected error")

        client = RemediationClient(remediation_config)

        with pytest.raises(
            RemediationError, match="Unexpected error during remediation"
        ):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_with_context(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with full context"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful remediation response
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.return_value = {
            "success": True,
            "message": "Remediation completed successfully",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)

        context = {
            "timestamp": "2025-01-01T00:00:00Z",
            "hostname": "test-server",
            "cpu_percent": 95.0,
        }

        result = client.trigger_remediation("high_cpu", context)

        assert result is True

        # Verify the context was passed correctly
        call_args = mock_requests_session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["context"] == context
        assert json_data["timestamp"] == "2025-01-01T00:00:00Z"
        assert json_data["hostname"] == "test-server"

    @pytest.mark.unit
    def test_get_service_status_success_new_api(
        self, mock_requests_session, remediation_config
    ):
        """Test successful service status retrieval using new API"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful status response
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "running",
            "uptime": "1:23:45",
            "version": "2.0.0",
        }

        mock_requests_session.get.side_effect = [
            mock_health_response,
            mock_status_response,
        ]

        client = RemediationClient(remediation_config)
        result = client.get_service_status()

        assert result["status"] == "running"
        assert result["uptime"] == "1:23:45"
        assert result["version"] == "2.0.0"

    @pytest.mark.unit
    def test_get_service_status_fallback_to_legacy(
        self, mock_requests_session, remediation_config
    ):
        """Test service status retrieval falling back to legacy API"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock 404 for new API, success for legacy
        mock_404_response = Mock()
        mock_404_response.status_code = 404

        mock_legacy_response = Mock()
        mock_legacy_response.status_code = 200
        mock_legacy_response.json.return_value = {
            "status": "running",
            "version": "1.0.0",
        }

        # Health check, then new API (404), then legacy API (success)
        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.HTTPError(response=mock_404_response),
            mock_legacy_response,
        ]

        client = RemediationClient(remediation_config)
        result = client.get_service_status()

        assert result["status"] == "running"
        assert result["version"] == "1.0.0"

    @pytest.mark.unit
    def test_get_service_status_all_endpoints_fail(
        self, mock_requests_session, remediation_config
    ):
        """Test service status when all endpoints fail"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_error_response = Mock()
        mock_error_response.status_code = 500

        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.HTTPError(response=mock_error_response),
            requests.exceptions.HTTPError(response=mock_error_response),
        ]

        client = RemediationClient(remediation_config)

        with pytest.raises(ServiceUnavailableError):
            client.get_service_status()

    @pytest.mark.unit
    def test_get_service_status_request_exception(
        self, mock_requests_session, remediation_config
    ):
        """Test service status with request exception"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.ConnectionError("Connection failed"),
        ]

        client = RemediationClient(remediation_config)

        with pytest.raises(ServiceUnavailableError, match="Cannot get service status"):
            client.get_service_status()

    @pytest.mark.unit
    def test_get_available_actions_success_new_api(
        self, mock_requests_session, remediation_config
    ):
        """Test successful available actions retrieval using new API"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful actions response
        mock_actions_response = Mock()
        mock_actions_response.status_code = 200
        mock_actions_response.json.return_value = {
            "actions": ["high_cpu", "high_disk", "high_memory", "service_restart"]
        }

        mock_requests_session.get.side_effect = [
            mock_health_response,
            mock_actions_response,
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        assert result == ["high_cpu", "high_disk", "high_memory", "service_restart"]

    @pytest.mark.unit
    def test_get_available_actions_fallback_to_legacy(
        self, mock_requests_session, remediation_config
    ):
        """Test available actions retrieval falling back to legacy API"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock 404 for new API, success for legacy
        mock_404_response = Mock()
        mock_404_response.status_code = 404

        mock_legacy_response = Mock()
        mock_legacy_response.status_code = 200
        mock_legacy_response.json.return_value = {"actions": ["high_cpu", "high_disk"]}

        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.HTTPError(response=mock_404_response),
            mock_legacy_response,
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        assert result == ["high_cpu", "high_disk"]

    @pytest.mark.unit
    def test_get_available_actions_fallback_to_defaults(
        self, mock_requests_session, remediation_config
    ):
        """Test available actions fallback to default actions"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_error_response = Mock()
        mock_error_response.status_code = 500

        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.HTTPError(response=mock_error_response),
            requests.exceptions.HTTPError(response=mock_error_response),
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        # Should return default actions
        assert result == ["high_cpu", "high_disk", "high_memory", "service_restart"]

    @pytest.mark.unit
    def test_get_available_actions_request_exception(
        self, mock_requests_session, remediation_config
    ):
        """Test available actions with request exception"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.side_effect = [
            mock_health_response,
            requests.exceptions.ConnectionError("Connection failed"),
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        # Should return default actions
        assert result == ["high_cpu", "high_disk", "high_memory", "service_restart"]

    @pytest.mark.unit
    def test_session_configuration(self, remediation_config):
        """Test that the session is configured correctly"""
        with patch("clients.remediation.requests.Session") as mock_session_class, patch(
            "clients.remediation.HTTPAdapter"
        ) as mock_adapter_class, patch("clients.remediation.Retry") as mock_retry_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.return_value = Mock(status_code=200)

            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            mock_retry = Mock()
            mock_retry_class.return_value = mock_retry

            # Verify retry strategy was configured
            mock_retry_class.assert_called_once_with(
                total=remediation_config.retry_attempts,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST"],
            )

            # Verify adapter was configured
            mock_adapter_class.assert_called_once_with(max_retries=mock_retry)

            # Verify session was configured
            mock_session.mount.assert_any_call("http://", mock_adapter)
            mock_session.mount.assert_any_call("https://", mock_adapter)
            assert mock_session.timeout == remediation_config.timeout

    @pytest.mark.unit
    def test_trigger_remediation_http_error_no_response(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with HTTP error but no response object"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Create HTTPError without response
        http_error = requests.exceptions.HTTPError("Generic HTTP error")
        http_error.response = None

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = http_error

        client = RemediationClient(remediation_config)

        with pytest.raises(RemediationError):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_with_empty_context(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with empty context"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful remediation response
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.return_value = {
            "success": True,
            "message": "Remediation completed successfully",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_cpu", {})

        assert result is True

        # Verify empty context was handled
        call_args = mock_requests_session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["context"] == {}
        assert json_data["timestamp"] is None
        assert json_data["hostname"] is None

    @pytest.mark.unit
    def test_trigger_remediation_all_endpoints_fail(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation when all endpoints fail"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = [
            requests.exceptions.HTTPError("First endpoint failed"),
            requests.exceptions.HTTPError("Second endpoint failed"),
        ]

        client = RemediationClient(remediation_config)

        with pytest.raises(RemediationError):
            client.trigger_remediation("high_cpu")

    @pytest.mark.unit
    def test_trigger_remediation_with_none_context(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger with None context"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful remediation response
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.return_value = {
            "success": True,
            "message": "Remediation completed successfully",
        }

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_cpu", None)

        assert result is True

        # Verify None context was converted to empty dict
        call_args = mock_requests_session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["context"] == {}

    @pytest.mark.unit
    def test_get_logger_function(self):
        """Test the get_logger function"""
        from clients.remediation import get_logger

        logger = get_logger("test_logger")
        assert logger.name == "test_logger"

    @pytest.mark.unit
    def test_path_manipulation_import_logic(self):
        """Test the path manipulation logic for imports"""
        # This tests the sys.path manipulation code at the module level
        # We can't easily test this directly, but we can verify the imports work
        from clients.remediation import RemediationClient
        from config.models import RemediatorConfig

        # If imports work, the path manipulation worked
        assert RemediationClient is not None
        assert RemediatorConfig is not None

    @pytest.mark.unit
    def test_trigger_remediation_json_decode_error_with_success_response(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation trigger when JSON decode fails but response is 200"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock response that's 200 but can't be decoded as JSON
        mock_remediation_response = Mock()
        mock_remediation_response.status_code = 200
        mock_remediation_response.json.side_effect = ValueError(
            "No JSON object could be decoded"
        )
        mock_remediation_response.text = "Remediation completed successfully"
        mock_remediation_response.raise_for_status.return_value = None  # No exception

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.return_value = mock_remediation_response

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_cpu")

        assert result is True

    @pytest.mark.unit
    def test_trigger_remediation_legacy_endpoint_first_try(
        self, mock_requests_session, remediation_config
    ):
        """Test remediation where new API 404s immediately, then legacy works"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Create a proper 404 HTTPError for the new API
        mock_404_response = Mock()
        mock_404_response.status_code = 404
        http_404_error = requests.exceptions.HTTPError("404 Not Found")
        http_404_error.response = mock_404_response

        # Mock successful legacy response
        mock_legacy_response = Mock()
        mock_legacy_response.status_code = 200
        mock_legacy_response.json.return_value = {
            "success": True,
            "message": "Legacy remediation completed",
        }
        mock_legacy_response.raise_for_status.return_value = None

        mock_requests_session.get.return_value = mock_health_response
        mock_requests_session.post.side_effect = [http_404_error, mock_legacy_response]

        client = RemediationClient(remediation_config)
        result = client.trigger_remediation("high_cpu")

        assert result is True
        # Verify both endpoints were called
        assert mock_requests_session.post.call_count == 2

    @pytest.mark.unit
    def test_get_available_actions_missing_actions_key(
        self, mock_requests_session, remediation_config
    ):
        """Test get_available_actions when response doesn't have 'actions' key"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        # Mock successful response but without 'actions' key
        mock_actions_response = Mock()
        mock_actions_response.status_code = 200
        mock_actions_response.json.return_value = {"status": "ok"}  # No 'actions' key
        mock_actions_response.raise_for_status.return_value = None

        mock_requests_session.get.side_effect = [
            mock_health_response,
            mock_actions_response,
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        # Should return empty list when 'actions' key is missing
        assert result == []

    @pytest.mark.unit
    def test_get_service_status_request_exception_on_second_call(
        self, mock_requests_session, remediation_config
    ):
        """Test service status with request exception on the status call specifically"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.side_effect = [
            mock_health_response,  # Health check succeeds
            requests.exceptions.RequestException(
                "Network error on status call"
            ),  # Status call fails
        ]

        client = RemediationClient(remediation_config)

        with pytest.raises(ServiceUnavailableError):
            client.get_service_status()

    @pytest.mark.unit
    def test_get_available_actions_request_exception_on_second_call(
        self, mock_requests_session, remediation_config
    ):
        """Test available actions with request exception on the actions call specifically"""
        # Mock successful health check
        mock_health_response = Mock()
        mock_health_response.status_code = 200

        mock_requests_session.get.side_effect = [
            mock_health_response,  # Health check succeeds
            requests.exceptions.RequestException(
                "Network error on actions call"
            ),  # Actions call fails
        ]

        client = RemediationClient(remediation_config)
        result = client.get_available_actions()

        # Should return default actions when request fails
        assert result == ["high_cpu", "high_disk", "high_memory", "service_restart"]


class TestRemediationClientExceptions:
    """Test exception classes"""

    @pytest.mark.unit
    def test_remediation_error(self):
        """Test RemediationError exception"""
        error = RemediationError("Test error message")
        assert str(error) == "Test error message"

    @pytest.mark.unit
    def test_network_error(self):
        """Test NetworkError exception"""
        error = NetworkError("Network failed")
        assert str(error) == "Network failed"

    @pytest.mark.unit
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError exception"""
        error = ServiceUnavailableError("Service down")
        assert str(error) == "Service down"

    @pytest.mark.unit
    def test_eri_timeout_error(self):
        """Test EriTimeoutError exception"""
        error = EriTimeoutError("operation", 30)
        assert "operation" in str(error)
        assert "30" in str(error)


class TestRemediationClientIntegration:
    """Integration tests - require --run-integration flag"""

    @pytest.fixture(autouse=True)
    def check_integration_flag(self, request):
        """Check if integration tests should run"""
        if not request.config.getoption("--run-integration", default=False):
            pytest.skip("Integration tests skipped - use --run-integration to run them")

    @pytest.mark.integration
    def test_real_remediation_service_connection(self, remediation_config):
        """Test connection to real C# remediation service"""
        try:
            client = RemediationClient(remediation_config)
            status = client.get_service_status()
            assert isinstance(status, dict)
        except ServiceUnavailableError:
            pytest.skip("C# remediation service not running")

    @pytest.mark.integration
    def test_real_available_actions(self, remediation_config):
        """Test getting available actions from real service"""
        try:
            client = RemediationClient(remediation_config)
            actions = client.get_available_actions()
            assert isinstance(actions, list)
            assert len(actions) > 0
        except ServiceUnavailableError:
            pytest.skip("C# remediation service not running")
