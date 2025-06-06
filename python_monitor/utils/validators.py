import re
import ipaddress
from urllib.parse import urlparse
from python_monitor.utils.exceptions import ValidationError


def validate_slack_token(token):
    """
    Validate Slack bot token format.

    Args:
        token (str): The Slack token to validate

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If token is invalid
    """
    if not token:
        raise ValidationError("Slack token cannot be empty")

    if not isinstance(token, str):
        raise ValidationError("Slack token must be a string")

    # Bot tokens should start with xoxb-
    if not token.startswith("xoxb-"):
        raise ValidationError(
            "Invalid Slack token format. Bot tokens must start with 'xoxb-'"
        )

    # Basic format validation for xoxb tokens
    # Format is typically: xoxb-{team_id}-{bot_id}-{secret}
    parts = token.split("-")
    if len(parts) < 4:
        raise ValidationError(
            "Invalid Slack token format. Expected format: xoxb-{team_id}-{bot_id}-{secret}"
        )

    # Check that team_id and bot_id parts are numeric
    try:
        int(parts[1])  # team_id should be numeric
        int(parts[2])  # bot_id should be numeric
    except (ValueError, IndexError):
        raise ValidationError(
            "Invalid Slack token format. Team ID and Bot ID must be numeric"
        )

    # Check that the secret part exists and has reasonable length
    if len(parts) < 4 or len(parts[3]) < 20:
        raise ValidationError("Invalid Slack token format. Secret part is too short")

    return True


def validate_slack_channel(channel):
    """
    Validate Slack channel name format.

    Args:
        channel (str): The channel name to validate

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If channel name is invalid
    """
    if not channel:
        raise ValidationError("Slack channel cannot be empty")

    if not isinstance(channel, str):
        raise ValidationError("Slack channel must be a string")

    # Must start with #
    if not channel.startswith("#"):
        raise ValidationError("Slack channel must start with '#'")

    # Remove the # for validation
    channel_name = channel[1:]

    if not channel_name:
        raise ValidationError("Slack channel name cannot be empty after '#'")

    # Check length (max 80 characters for the name part, not including #)
    if len(channel_name) > 80:
        raise ValidationError("Slack channel name too long (max 80 characters)")

    # Check for valid characters: lowercase letters, numbers, hyphens, underscores
    if not re.match(r"^[a-z0-9_-]+$", channel_name):
        raise ValidationError(
            "Invalid Slack channel format. Must be #channel-name with lowercase letters, numbers, hyphens, or underscores"
        )

    return True


def validate_threshold(threshold, min_val=0, max_val=100):
    """
    Validate threshold value.

    Args:
        threshold: The threshold value to validate
        min_val (float): Minimum allowed value (default: 0)
        max_val (float): Maximum allowed value (default: 100)

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If threshold is invalid
    """
    if threshold is None:
        raise ValidationError("Threshold cannot be None")

    if not isinstance(threshold, (int, float)):
        raise ValidationError("Threshold must be a number")

    if threshold < min_val or threshold > max_val:
        raise ValidationError(f"Threshold must be between {min_val} and {max_val}")

    return True


def validate_url(url):
    """
    Validate URL format.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    if not isinstance(url, str):
        raise ValidationError("URL must be a string")

    try:
        parsed = urlparse(url)

        # Must have a scheme (http or https)
        if parsed.scheme not in ["http", "https"]:
            raise ValidationError("URL must use http or https scheme")

        # Must have a netloc (domain/host)
        if not parsed.netloc:
            raise ValidationError("URL must have a valid host")

        return True

    except Exception as e:
        raise ValidationError(f"Invalid URL format: {str(e)}")


def validate_hostname(hostname):
    """
    Validate hostname according to RFC standards.

    Args:
        hostname (str): The hostname to validate

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If hostname is invalid
    """
    if not hostname:
        raise ValidationError("Hostname cannot be empty")

    if not isinstance(hostname, str):
        raise ValidationError("Hostname must be a string")

    if len(hostname) > 253:
        raise ValidationError("Hostname too long (max 253 characters)")

    # Check if it's an IP address (which is valid as hostname)
    try:
        ipaddress.ip_address(hostname)
        return True  # Valid IP address
    except ValueError:
        pass  # Not an IP, continue with hostname validation

    # Hostname validation
    if hostname.startswith("-") or hostname.endswith("-"):
        raise ValidationError("Hostname cannot start or end with hyphen")

    if ".." in hostname:
        raise ValidationError("Hostname cannot contain consecutive dots")

    # Check for invalid characters (only alphanumeric, hyphens, and dots allowed)
    if not re.match(r"^[a-zA-Z0-9.-]+$", hostname):
        raise ValidationError("Hostname contains invalid characters")

    # Check each label (part between dots)
    labels = hostname.split(".")
    for label in labels:
        if not label:  # Empty label
            raise ValidationError("Hostname cannot have empty labels")
        if len(label) > 63:
            raise ValidationError("Hostname label too long (max 63 characters)")
        if label.startswith("-") or label.endswith("-"):
            raise ValidationError("Hostname label cannot start or end with hyphen")

    return True
