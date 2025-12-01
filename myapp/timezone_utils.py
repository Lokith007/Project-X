"""
Timezone utilities for converting between UTC and user's local timezone.
"""
import pytz
from django.utils import timezone as django_timezone


def get_user_timezone(user):
    """
    Get user's timezone object.
    
    Args:
        user: Django User object (should have .info attribute)
    
    Returns:
        pytz timezone object
    """
    if user and hasattr(user, 'info') and user.info.timezone:
        try:
            return pytz.timezone(user.info.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            pass
    return pytz.UTC


def to_user_timezone(dt, user):
    """
    Convert UTC datetime to user's local timezone.
    
    Args:
        dt: datetime object (should be timezone-aware)
        user: Django User object
    
    Returns:
        datetime in user's timezone
    """
    user_tz = get_user_timezone(user)
    
    if django_timezone.is_naive(dt):
        dt = django_timezone.make_aware(dt, django_timezone.utc)
    
    return dt.astimezone(user_tz)


def user_now(user):
    """
    Get current datetime in user's timezone.
    
    Args:
        user: Django User object
    
    Returns:
        datetime in user's timezone
    """
    return django_timezone.now().astimezone(get_user_timezone(user))


def user_today(user):
    """
    Get today's date in user's timezone.
    
    Args:
        user: Django User object
    
    Returns:
        date object in user's timezone
    """
    return user_now(user).date()


def get_common_timezones():
    """
    Get list of common timezone choices for forms.
    
    Returns:
        List of (timezone_name, timezone_display) tuples
    """
    # Group by continent for better UX
    timezones = []
    for tz in pytz.common_timezones:
        # Create display name
        display = tz.replace('_', ' ')
        timezones.append((tz, display))
    return timezones
