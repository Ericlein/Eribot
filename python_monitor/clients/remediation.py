"""
Remediation client for communicating with the C# remediation service.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports during transition
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import local modules after path setup
from config.models import RemediatorConfig


def get_logger(name):
    return logging.getLogger(name)


class RemediationError(Exception):
    """Exception raised when remediation operations fail."""
    pass


class NetworkError(Exception):
    """Exception raised when network operations fail."""
    pass


class ServiceUnavailableError(Exception):
    """Exception raised when a service is unavailable."""
    pass


class EriTimeoutError(Exception):
    """Exception raised when operations timeout."""
    pass


class RemediationClient:
    """Client for communicating with the C# remediation service."""
    
    def __init__(self, config: RemediatorConfig):
        self.config = config
        self.logger = get_logger('remediation_client')
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['HEAD', 'GET', 'POST']
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Set timeout
        self.session.timeout = config.timeout
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to remediation service."""
        try:
            response = self.session.get(
                f'{self.config.url}/health', timeout=5
            )
            if response.status_code == 200:
                self.logger.info('Remediation service is available')
                return True
            else:
                self.logger.warning(
                    f'Remediation service returned status: '
                    f'{response.status_code}'
                )
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f'Remediation service not available: {e}')
            return False
    
    def trigger_remediation(
        self, issue_type: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Trigger a remediation action."""
        try:
            payload = {
                'issueType': issue_type,
                'context': context or {},
                'timestamp': context.get('timestamp') if context else None,
                'hostname': context.get('hostname') if context else None
            }
            
            self.logger.info(f'Triggering remediation for: {issue_type}')
            
            # Try the new API endpoint first, then fall back to legacy
            urls_to_try = [
                f'{self.config.url}/api/remediation/execute',
                f'{self.config.url}/remediate'
            ]
            
            for url in urls_to_try:
                try:
                    response = self.session.post(
                        url,
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
                            self.logger.info(
                                f'Remediation successful: {message}'
                            )
                            return True
                        else:
                            raise RemediationError(
                                f'Remediation failed: {message}'
                            )
                            
                    except ValueError:
                        # Response is not JSON, treat as success if status is 200
                        self.logger.info(
                            f'Remediation successful: {response.text}'
                        )
                        return True
                    
                except requests.exceptions.HTTPError as e:
                    if (e.response.status_code == 404 and 
                        url == urls_to_try[0]):
                        # Try the legacy endpoint
                        continue
                    else:
                        raise
                        
            # If we get here, all URLs failed
            raise RemediationError('All remediation endpoints failed')
            
        except requests.exceptions.Timeout:
            raise EriTimeoutError('remediation', self.config.timeout)
            
        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError(
                'Could not connect to remediation service'
            )
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            
            if status_code == 400:
                raise RemediationError('Invalid remediation request')
            elif status_code == 404:
                raise RemediationError(f'Unknown issue type: {issue_type}')
            elif status_code == 503:
                raise ServiceUnavailableError(
                    'Remediation service temporarily unavailable'
                )
            else:
                raise RemediationError(f'HTTP error {status_code}: {e}')
                
        except Exception as e:
            raise RemediationError(
                f'Unexpected error during remediation: {str(e)}'
            )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of the remediation service."""
        try:
            # Try new API first, then legacy
            urls_to_try = [
                f'{self.config.url}/api/remediation/status',
                f'{self.config.url}/status'
            ]
            
            for url in urls_to_try:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as e:
                    if (e.response.status_code == 404 and 
                        url == urls_to_try[0]):
                        continue
                    else:
                        raise
                        
            raise ServiceUnavailableError('All status endpoints failed')
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Error getting service status: {e}')
            raise ServiceUnavailableError(
                f'Cannot get service status: {e}'
            )
    
    def get_available_actions(self) -> List[str]:
        """Get list of available remediation actions."""
        try:
            # Try new API first, then legacy
            urls_to_try = [
                f'{self.config.url}/api/remediation/actions',
                f'{self.config.url}/actions'
            ]
            
            for url in urls_to_try:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    return data.get('actions', [])
                except requests.exceptions.HTTPError as e:
                    if (e.response.status_code == 404 and 
                        url == urls_to_try[0]):
                        continue
                    else:
                        raise
                        
            # Fallback to common actions if endpoints not available
            return [
                'high_cpu', 'high_disk', 'high_memory', 'service_restart'
            ]
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Error getting available actions: {e}')
            return [
                'high_cpu', 'high_disk', 'high_memory', 'service_restart'
            ]