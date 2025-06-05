import requests
import logging
from typing import Dict, Any, Optional
from config_loader import RemediatorConfig

class RemediationClient:
    def __init__(self, config: RemediatorConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = 30  # 30 second timeout
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test if the remediation service is available"""
        try:
            response = self.session.get(f"{self.config.url}/health", timeout=5)
            if response.status_code == 200:
                self.logger.info("Remediation service is available")
                return True
            else:
                self.logger.warning(f"Remediation service returned status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Remediation service not available: {e}")
            return False
    
    def trigger_remediation(self, issue_type: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Trigger remediation for a specific issue type
        
        Args:
            issue_type: Type of issue ('high_cpu', 'high_disk', etc.)
            context: Additional context information about the issue
            
        Returns:
            bool: True if remediation was triggered successfully
        """
        try:
            payload = {
                "issueType": issue_type,
                "context": context or {},
                "timestamp": context.get('timestamp') if context else None
            }
            
            self.logger.info(f"Triggering remediation for: {issue_type}")
            
            response = self.session.post(
                f"{self.config.url}/remediate",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            result_text = response.text
            self.logger.info(f"Remediation successful: {result_text}")
            
            # TODO Send update to Slack if we have a slack client
            try:
                from slack_client import SlackClient
                # This is a bit of a hack - in a real app you'd inject dependencies properly
                import os
                from config_loader import SlackConfig
                
                slack_config = SlackConfig(
                    channel=os.getenv('SLACK_CHANNEL', '#devops-alerts'),
                    token=os.getenv('SLACK_BOT_TOKEN', '')
                )
                
                if slack_config.token:
                    slack_client = SlackClient(slack_config)
                    slack_client.send_remediation_update(issue_type, result_text, True)
            except Exception as e:
                self.logger.debug(f"Could not send Slack update: {e}")
            
            return True
            
        except requests.exceptions.Timeout:
            error_msg = f"Remediation request timed out for {issue_type}"
            self.logger.error(error_msg)
            self._send_error_notification(issue_type, error_msg)
            return False
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Could not connect to remediation service for {issue_type}"
            self.logger.error(error_msg)
            self._send_error_notification(issue_type, error_msg)
            return False
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error during remediation for {issue_type}: {e.response.status_code}"
            self.logger.error(error_msg)
            self._send_error_notification(issue_type, error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error during remediation for {issue_type}: {str(e)}"
            self.logger.error(error_msg)
            self._send_error_notification(issue_type, error_msg)
            return False
    
    def _send_error_notification(self, issue_type: str, error_msg: str) -> None:
        """Send error notification to Slack"""
        try:
            from slack_client import SlackClient
            import os
            from config_loader import SlackConfig
            
            slack_config = SlackConfig(
                channel=os.getenv('SLACK_CHANNEL', '#devops-alerts'),
                token=os.getenv('SLACK_BOT_TOKEN', '')
            )
            
            if slack_config.token:
                slack_client = SlackClient(slack_config)
                slack_client.send_remediation_update(issue_type, error_msg, False)
        except Exception as e:
            self.logger.debug(f"Could not send error notification to Slack: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of the remediation service"""
        try:
            response = self.session.get(f"{self.config.url}/status", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_available_actions(self) -> list:
        """Get list of available remediation actions"""
        try:
            response = self.session.get(f"{self.config.url}/actions", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting available actions: {e}")
            return []