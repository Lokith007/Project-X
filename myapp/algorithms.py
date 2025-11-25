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
    user = request.user
    info = user.info
    following_users = set(info.get_following())
    following_orgs = set(info.followed_organization.all())
    current_time = now()

    def compute_score(item, creator, is_followed):
        created_at = getattr(item, 'created_at', None) or current_time
        time_diff = (current_time - created_at).total_seconds()

        decay_rate = 1 / (60 * 60 * 6)
        boost_weight = 100_000
        boost = boost_weight * (0.5 ** (time_diff * decay_rate)) if is_followed else 0
        return -time_diff + boost

    def annotate_items(queryset, type_name, user_check, org_check):
        annotated = []
        for item in queryset:
            item.feed_type = type_name
            item.created_at = getattr(item, 'created_at', item.id)
            is_followed = (
                (hasattr(item, 'user') and item.user in user_check) or
                (hasattr(item, 'creator') and item.creator in user_check) or
                (hasattr(item, 'Organization') and item.Organization in org_check) or
                (hasattr(item, 'organization') and item.organization in org_check)
            )
            item._score = compute_score(item, None, is_followed)
            annotated.append(item)
        return annotated

    posts = annotate_items(post.objects.all().order_by('-id'), 'post', following_users, following_orgs)

    if type == 'all':
        combined = sorted(list(posts), key=lambda item: item._score, reverse=True)
    elif type == 'following':
        combined = [item for item in posts
                    if item._score > -3600 * 24 * 7]
        combined = sorted([item for item in combined
            if (hasattr(item, 'user') and item.user in following_users)],
            key=lambda item: item._score, reverse=True)
    elif type == 'trending':
        combined = sorted(list(posts), key=lambda item: item.created_at, reverse=True)
    else:
        combined = []

    # Pagination
    paginator = Paginator(combined, per_page)
    # return paginator.get_page(page)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return paginator.get_page(1)[:0]  # Return empty page
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