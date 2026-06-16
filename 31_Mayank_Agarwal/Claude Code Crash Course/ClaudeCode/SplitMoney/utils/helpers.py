from datetime import datetime


def format_date(date_obj, format_string="%B %d, %Y"):
    """Format a date object to a readable string.

    Args:
        date_obj: datetime.date or datetime.datetime object
        format_string: strftime format string (default: "Month Day, Year")

    Returns:
        Formatted date string
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_string)
    return date_obj.strftime(format_string)


def format_time(time_obj, format_string="%I:%M %p"):
    """Format a time object to a readable string.

    Args:
        time_obj: datetime.time or datetime.datetime object
        format_string: strftime format string (default: "HH:MM AM/PM")

    Returns:
        Formatted time string
    """
    if isinstance(time_obj, datetime):
        return time_obj.strftime(format_string)
    return time_obj.strftime(format_string)


def format_datetime(dt_obj, format_string="%B %d, %Y at %I:%M %p"):
    """Format a datetime object to a readable string.

    Args:
        dt_obj: datetime.datetime object
        format_string: strftime format string

    Returns:
        Formatted datetime string
    """
    return dt_obj.strftime(format_string)
