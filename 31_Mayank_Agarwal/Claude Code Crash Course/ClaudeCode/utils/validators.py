import re


def validate_email(email):
    """Validate if a string is a valid email address.

    Args:
        email: Email string to validate

    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate if a string is a valid phone number.

    Args:
        phone: Phone number string to validate (supports various formats)

    Returns:
        True if valid phone format, False otherwise
    """
    pattern = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$'
    return re.match(pattern, phone.replace(' ', '')) is not None


def validate_username(username, min_length=3, max_length=20):
    """Validate if a string is a valid username.

    Args:
        username: Username string to validate
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 20)

    Returns:
        True if valid username format, False otherwise
    """
    if not (min_length <= len(username) <= max_length):
        return False
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, username) is not None


def validate_url(url):
    """Validate if a string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL format, False otherwise
    """
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return re.match(pattern, url) is not None
