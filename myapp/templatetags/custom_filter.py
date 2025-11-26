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

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def args(obj, arg):
    if not obj:
        return [arg]
    if isinstance(obj, list):
        obj.append(arg)
        return obj
    return [obj, arg]

@register.filter
def call(obj, method_name):
    if isinstance(obj, list):
        # obj is actually [real_obj, arg1, arg2, ...]
        real_obj = obj[0]
        args = obj[1:]
        method = getattr(real_obj, method_name)
        return method(*args)
    method = getattr(obj, method_name)
    return method()