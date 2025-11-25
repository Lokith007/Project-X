from django.core.paginator import Paginator, EmptyPage
from itertools import chain
from .models import follow, skill
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta

def get_explore_users(filter_dev, request, count=200, order_by='-created_at'):
    # Step 1: Get followed user IDs and current user ID
    followed_ids = follow.objects.filter(
        follower=request.user.info
    ).values_list('following_id', flat=True)

    exclude_ids = list(followed_ids) + [request.user.info.id]

    # Step 2: Use `.only()` to limit fields fetched from DB for performance
    users = filter_dev.exclude(id__in=exclude_ids).only('id', 'profile_image', 'user__username').order_by(order_by)[:count]
    return users


def get_personalized_feed(request, type='all', page=1, per_page=7):
    """
    MOCK ALGORITHM - Simple log feed for home page.
    TODO: Replace with advanced recommendation algorithm later.
    Currently just returns recent logs with basic filtering.
    """
    from logs.models import Log
    
    # Simple mock: just get recent logs
    # Type parameter is ignored for now in mock version
    logs = Log.objects.select_related('user__user').order_by('-timestamp')
    
    # Annotate each log with feed_type for template compatibility
    for log in logs:
        log.feed_type = 'log'
    
    # Pagination
    paginator = Paginator(logs, per_page)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return paginator.get_page(1)[:0]
    
    return page_obj

def top_skills_list():
    top_skills = list(skill.objects.all()[0:10])     # Programming Languages
    top_skills += list(skill.objects.all()[40:50])   # Frameworks and Libraries
    top_skills += list(skill.objects.all()[80:87])   # Databases
    top_skills += list(skill.objects.all()[100:103]) # Cloud Platforms
    top_skills += list(skill.objects.all()[125:127]) # Version Control
    top_skills += list(skill.objects.all()[150:152]) # Backend Frameworks
    top_skills += list(skill.objects.all()[180:182]) # AI/ML
    return top_skills