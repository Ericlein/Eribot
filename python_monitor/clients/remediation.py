"""
Remediation client for EriBot.

Refactored from remediation_client.py with better error handling and structure.
"""

import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from python_monitor.config.models import RemediatorConfig
from python_monitor.utils.logger import get_logger
from python_monitor.utils.exceptions import (
    RemediationError, 
    NetworkError, 
    ServiceUnavailableError,
    TimeoutError as EriTimeoutError
)


class RemediationClient:
    """Enhanced remediation client with retry logic and better error handling."""
    
    def __init__(self, config: RemediatorConfig):
        """
        Initialize remediation client.
        
        Args:
            config: Remediator configuration
        """
        self.config = config
        self.logger = get_logger("remediation_client")
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set timeout
        self.session.timeout = config.timeout
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test if the remediation service is available."""
        try:
            response = self.session.get(f"{self.config.url}/health", timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ Remediation service is available")
                return True
            else:
                self.logger.warning(f"Remediation service returned status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Remediation service not available: {e}")
            return False
    
    def trigger_remediation(
        self, 
        issue_type: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Trigger remediation for a specific issue type.
        
        Args:
            issue_type: Type of issue ('high_cpu', 'high_disk', etc.)
            context: Additional context information about the issue
            
        Returns:
            True if remediation was triggered successfully
            
        Raises:
            RemediationError: If remediation fails
            NetworkError: If network communication fails
            ServiceUnavailableError: If service is not available
        """
        try:
            payload = {
                "issueType": issue_type,
                "context": context or {},
                "timestamp": context.get('timestamp') if context else None,
                "hostname": context.get('hostname') if context else None
            }
            
            self.logger.info(f"Triggering remediation for: {issue_type}")
            self.logger.debug(f"Payload: {payload}")
            
            response = self.session.post(
                f"{self.config.url}/api/remediation/execute",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                result_data = response.json()
                success = result_data.get('success', True)
                message = result_data.get('message', response.text)
                
                if success:
                    self.logger.info(f"Remediation successful: {message}")
                    return True
                else:
                    raise RemediationError(f"Remediation failed: {message}")
                    
            except ValueError:
                # Response is not JSON, treat as success if status is 200
                self.logger.info(f"Remediation successful: {response.text}")
                return True
            
        except requests.exceptions.Timeout:
            raise EriTimeoutError("remediation", self.config.timeout)
            
        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError("Could not connect to remediation service")
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            
            if status_code == 400:
                raise RemediationError("Invalid remediation request")
            elif status_code == 404:
                raise RemediationError(f"Unknown issue type: {issue_type}")
            elif status_code == 503:
                raise ServiceUnavailableError("Remediation service temporarily unavailable")
            else:
                raise RemediationError(f"HTTP error {status_code}: {e}")
                
        except Exception as e:
            raise RemediationError(f"Unexpected error during remediation: {str(e)}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of the remediation service.
        
        Returns:
            Service status information
            
        Raises:
            ServiceUnavailableError: If service is not available
        """
        try:
            response = self.session.get(
                f"{self.config.url}/api/remediation/status",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting service status: {e}")
            raise ServiceUnavailableError(f"Cannot get service status: {e}")
    
    def get_available_actions(self) -> List[str]:
        """
        Get list of available remediation actions.
        
        Returns:
            List of available action types
            
        Raises:
            ServiceUnavailableError: If service is not available
        """
        try:
            response = self.session.get(
                f"{self.config.url}/api/remediation/actions",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('actions', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting available actions: {e}")
            raise ServiceUnavailableError(f"Cannot get available actions: {e}")
    
    def validate_action(self, issue_type: str) -> bool:
        """
        Validate if an action type is supported.
        
        Args:
            issue_type: The issue type to validate
            
        Returns:
            True if action is supported
        """
        try:
            available_actions = self.get_available_actions()
            return issue_type in available_actions
        except Exception as e:
            self.logger.warning(f"Could not validate action {issue_type}: {e}")
            return False