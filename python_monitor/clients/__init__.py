"""
Client modules for external service integrations.

Contains clients for Slack, remediation services, and other external APIs.
"""

from .slack import SlackClient
from .remediation import RemediationClient

__all__ = [
    "SlackClient",
    "RemediationClient",
]