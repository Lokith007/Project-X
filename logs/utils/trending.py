"""
Trending logs utility - Calculate engagement scores for hot/trending content
"""
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta
from logs.models import Log


def get_trending_logs(limit=5, hours=24):
    """
    Get trending logs based on engagement in the last N hours
    
    Engagement Score = (reactions * 2) + (comments * 3) + (replies * 3)
    - Used for ranking only
    - Display shows actual count of unique engaged users
    
    Args:
        limit: Number of trending logs to return (default 5)
        hours: Time window in hours (default 24)
    
    Returns:
        QuerySet of Log objects with engagement_score and total_engaged_users annotations
    """
    cutoff_time = timezone.now() - timedelta(hours=hours)
    
    # Annotate logs with engagement metrics
    trending_logs = Log.objects.filter(
        timestamp__gte=cutoff_time
    ).select_related(
        'user__user',
        'user__coding_style'
    ).prefetch_related(
        'reactions__user',
        'comments__user'
    ).annotate(
        # Count individual engagement types
        reaction_count=Count('reactions__user', distinct=True),
        comment_count=Count('comments', filter=Q(comments__parent_comment__isnull=True), distinct=True),
        reply_count=Count('comments', filter=Q(comments__parent_comment__isnull=False), distinct=True),
    ).annotate(
        # Calculate engagement score for ranking: reactions*2 + comments*3 + replies*3
        engagement_score=F('reaction_count') * 2 + F('comment_count') * 3 + F('reply_count') * 3
    ).filter(
        engagement_score__gt=0  # Only show logs with engagement
    ).order_by('-engagement_score')[:limit]
    
    # Calculate actual unique engaged users (to avoid double counting)
    # A user who reacts AND comments should be counted once, not twice
    trending_logs = list(trending_logs)  # Evaluate QuerySet to allow modification
    
    for log in trending_logs:
        engaged_users = set()
        
        # Add all users who reacted (uses prefetched data, no extra query)
        engaged_users.update(log.reactions.values_list('user_id', flat=True))
        
        # Add all users who commented or replied (uses prefetched data, no extra query)
        engaged_users.update(log.comments.values_list('user_id', flat=True))
        
        # Set the actual unique count
        log.total_engaged_users = len(engaged_users)
    
    return trending_logs


def get_engagement_count(log):
    """
    Get total engagement count for a log (for display purposes)
    
    Args:
        log: Log object (should have engagement_score annotation)
    
    Returns:
        Integer total engagement count
    """
    if hasattr(log, 'engagement_score'):
        return log.engagement_score
    
    # Fallback: calculate on the fly
    reactions = log.reactions.count()
    comments = log.comments.filter(parent_comment__isnull=True).count()
    replies = log.comments.filter(parent_comment__isnull=False).count()
    
    return (reactions * 2) + (comments * 3) + (replies * 3)


def format_engagement_text(engagement_count):
    """
    Format engagement count for display
    
    Args:
        engagement_count: Integer engagement score
    
    Returns:
        Formatted string like "15+ engaging" or "40+ engaging"
    """
    if engagement_count >= 100:
        return f"{engagement_count}+ engaging right now"
    elif engagement_count >= 10:
        return f"{engagement_count}+ engaging right now"
    else:
        return f"{engagement_count} engaging right now"
