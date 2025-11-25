from django import template
from myapp.models import follow
import urllib.parse
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def is_following(user,otheruser):
    return follow.objects.filter(follower = user, following = otheruser).exists()



@register.filter
def lstrip(value):
    return value.strip()

@register.filter
def is_online(last_seen):
    if not last_seen:
        return False
    now = timezone.now()
    return now - last_seen < timedelta(minutes=5)