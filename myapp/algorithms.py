from django.core.paginator import Paginator, EmptyPage
from itertools import chain
from .models import follow, skill, userinfo
from django.db.models import Q, Count, Exists, OuterRef, Subquery, Value, FloatField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from datetime import timedelta
import random


def get_explore_users(filter_dev, request, count=200, order_by='-created_at'):
    # Step 1: Get followed user IDs and current user ID
    followed_ids = follow.objects.filter(
        follower=request.user.info
    ).values_list('following_id', flat=True)

    exclude_ids = list(followed_ids) + [request.user.info.id]

    # Step 2: Use `.only()` to limit fields fetched from DB for performance
    users = filter_dev.exclude(id__in=exclude_ids).only('id', 'profile_image', 'user__username').order_by(order_by)[:count]
    return users


# =============================================================================
# RECENCY MULTIPLIERS - How much to boost logs based on age
# =============================================================================
RECENCY_MULTIPLIERS = [
    (timedelta(hours=1), 10.0),     # < 1 hour: 10x boost (very fresh)
    (timedelta(hours=6), 6.0),      # 1-6 hours: 6x boost
    (timedelta(hours=24), 3.0),     # 6-24 hours: 3x boost
    (timedelta(days=3), 1.5),       # 1-3 days: 1.5x boost
    (timedelta(days=7), 0.5),       # 3-7 days: 0.5x
    (None, 0.1),                    # > 7 days: 0.1x (very old)
]

# =============================================================================
# FRESHNESS PENALTIES - Aggressive down-weight for already-interacted logs
# These are designed to push viewed content DOWN regardless of engagement
# =============================================================================
FRESHNESS_PENALTY_VIEWED = 0.15     # User has seen this log - drop to 15%
FRESHNESS_PENALTY_REACTED = 0.05    # User reacted to this log - drop to 5%
FRESHNESS_PENALTY_COMMENTED = 0.02  # User commented on this log - drop to 2%

# =============================================================================
# ENGAGEMENT SCORE CAP - Prevent high-engagement logs from dominating
# =============================================================================
ENGAGEMENT_SCORE_CAP = 10.0  # Cap engagement contribution to prevent stale popular logs

# =============================================================================
# SECONDARY NETWORK CONFIG
# =============================================================================
SECONDARY_NETWORK_RATIO = 0.25  # 25% of feed from friends-of-friends


def get_recency_multiplier(log_timestamp):
    """Calculate recency multiplier based on log age."""
    age = now() - log_timestamp
    for threshold, multiplier in RECENCY_MULTIPLIERS:
        if threshold is None or age <= threshold:
            return multiplier
    return 0.2  # Default for very old logs


def calculate_engagement_score(log):
    """
    Calculate base engagement score for a log.
    Formula: reactions * 1.5 + comments * 2.0 + views * 0.1
    Capped at ENGAGEMENT_SCORE_CAP to prevent high-engagement logs from dominating.
    """
    reaction_count = getattr(log, 'reaction_count', 0) or 0
    comment_count = getattr(log, 'comment_count', 0) or 0
    view_count = getattr(log, 'total_views', 0) or 0
    
    raw_score = (reaction_count * 1.5) + (comment_count * 2.0) + (view_count * 0.1)
    # Cap engagement to prevent popular logs from staying at top forever
    return min(raw_score, ENGAGEMENT_SCORE_CAP)


def get_interaction_status(log_id, viewed_log_ids, reacted_log_ids, commented_log_ids):
    """
    Get the interaction status and corresponding penalty for a log.
    Returns (penalty, interaction_type) tuple.
    """
    if log_id in commented_log_ids:
        return (FRESHNESS_PENALTY_COMMENTED, 'commented')
    elif log_id in reacted_log_ids:
        return (FRESHNESS_PENALTY_REACTED, 'reacted')
    elif log_id in viewed_log_ids:
        return (FRESHNESS_PENALTY_VIEWED, 'viewed')
    return (1.0, None)


def calculate_log_score(log, user, viewed_log_ids, reacted_log_ids, commented_log_ids, is_secondary=False):
    """
    Calculate final score for a log using a RECENCY-FIRST formula.
    
    NEW FORMULA (recency dominates):
    Score = (recency_multiplier * 10) + (capped_engagement * freshness_penalty)
    
    This ensures:
    - Fresh unseen logs ALWAYS rank higher than old seen logs
    - Engagement only matters for tie-breaking among similar-age logs
    - Viewed/interacted logs drop significantly regardless of engagement
    
    If is_secondary (friend-of-friend), apply additional 0.7x multiplier
    """
    # Base engagement (capped to prevent domination)
    engagement_score = calculate_engagement_score(log)
    
    # Recency boost - THIS IS THE PRIMARY RANKING FACTOR
    recency = get_recency_multiplier(log.timestamp)
    
    # Freshness penalty based on deepest interaction
    freshness, interaction_type = get_interaction_status(
        log.id, viewed_log_ids, reacted_log_ids, commented_log_ids
    )
    
    # Store interaction type for recommendation labels
    log.user_interaction = interaction_type
    
    # NEW SCORING FORMULA: Recency is primary, engagement is secondary
    # Recency score: dominates ranking (0-100 range)
    recency_score = recency * 10
    
    # Engagement bonus: only affects similar-recency logs (0-10 range, reduced by freshness)
    engagement_bonus = engagement_score * freshness
    
    # If user has interacted, HEAVILY penalize the recency score too
    if interaction_type:
        recency_score *= freshness
    
    # Final score
    score = recency_score + engagement_bonus
    
    # Secondary network gets lower priority than direct network
    if is_secondary:
        score *= 0.7
    
    return score


def get_user_interaction_sets(user):
    """
    Get sets of log IDs that the user has interacted with.
    Used for calculating freshness penalties.
    
    Returns three sets for each user (isolated per user):
    - viewed_log_ids: Logs the user has viewed
    - reacted_log_ids: Logs the user has reacted to
    - commented_log_ids: Logs the user has commented OR replied on
    """
    from logs.models import LogViews, Reaction, Comment
    
    # Logs viewed by this specific user
    viewed_log_ids = set(
        LogViews.objects.filter(user=user)
        .values_list('log_id', flat=True)
    )
    
    # Logs this specific user has reacted to
    reacted_log_ids = set(
        Reaction.objects.filter(user=user)
        .values_list('mindlog_id', flat=True)
    )
    
    # Logs this specific user has commented on (includes replies)
    # Both top-level comments and replies have mindlog_id pointing to the log
    commented_log_ids = set(
        Comment.objects.filter(user=user)
        .values_list('mindlog_id', flat=True)
    )
    
    return viewed_log_ids, reacted_log_ids, commented_log_ids


def get_network_user_ids(user):
    """
    Get IDs of users that the current user follows (primary/direct network).
    Each user has their own isolated network.
    """
    return set(
        follow.objects.filter(follower=user)
        .values_list('following_id', flat=True)
    )


def get_secondary_network_user_ids(user, primary_network_ids):
    """
    Get friends-of-friends: users followed by people the user follows,
    excluding:
    - The current user themselves
    - Users already in primary network (direct follows)
    
    This creates a secondary network unique to each user.
    """
    if not primary_network_ids:
        return set()
    
    # Users followed by people I follow
    secondary_ids = set(
        follow.objects.filter(follower_id__in=primary_network_ids)
        .exclude(following=user)  # Exclude self
        .exclude(following_id=user.id)  # Also exclude by ID
        .exclude(following_id__in=primary_network_ids)  # Exclude direct follows
        .values_list('following_id', flat=True)
    )
    return secondary_ids


def _get_secondary_recommendation_reason(log, current_user, primary_network_ids):
    """
    Generate recommendation reason for SECONDARY NETWORK logs only.
    Similar to LinkedIn/Instagram "Followed by X" or "Suggested for you" labels.
    
    Returns a dict with:
    - text: The display text (e.g., "Followed by @john")
    - subtext: Optional secondary text
    - icon: Icon class for display
    """
    log_author = log.user
    
    if not primary_network_ids:
        return {
            'text': 'Suggested for you',
            'subtext': None,
            'icon': 'fa-user-plus'
        }
    
    # Find who from user's network follows this author
    mutual_follows = follow.objects.filter(
        follower_id__in=primary_network_ids,
        following=log_author
    ).select_related('follower__user')[:3]
    
    if mutual_follows:
        names = [f.follower.user.username for f in mutual_follows]
        count = len(names)
        
        if count == 1:
            return {
                'text': f'@{names[0]} follows',
                'subtext': None,
                'icon': 'fa-user-check'
            }
        elif count == 2:
            return {
                'text': f'@{names[0]} and @{names[1]} follow',
                'subtext': None,
                'icon': 'fa-users'
            }
        else:
            # Check total count for "and X others"
            total_count = follow.objects.filter(
                follower_id__in=primary_network_ids,
                following=log_author
            ).count()
            others = total_count - 1
            return {
                'text': f'@{names[0]} and {others} others follow',
                'subtext': None,
                'icon': 'fa-users'
            }
    
    return {
        'text': 'Suggested for you',
        'subtext': 'Based on your network',
        'icon': 'fa-lightbulb-o'
    }


def get_personalized_feed(request, type='network', page=1, per_page=7, cursor=None):
    """
    Advanced personalized feed algorithm with recency boost and freshness penalties.
    
    Feed types:
    - 'network': Logs from followed users + secondary network suggestions
    - 'local': Logs from same location/organization (future)
    - 'global': All logs, globally ranked
    
    Scoring Formula:
    Score = (engagement_score + 1) * recency_multiplier * freshness_penalty
    
    Where:
    - engagement_score = reactions * 1.5 + comments * 2.0 + views * 0.1
    - recency_multiplier = 5.0 (< 1hr) to 0.2 (> 7 days)
    - freshness_penalty = 0.3 (viewed), 0.1 (reacted), 0.05 (commented)
    """
    from logs.models import Log, Reaction, Comment
    
    user = request.user.info
    
    # Get user interaction history for freshness calculation
    viewed_log_ids, reacted_log_ids, commented_log_ids = get_user_interaction_sets(user)
    
    # Get primary network (users I follow)
    primary_network_ids = get_network_user_ids(user)
    
    # Base queryset with annotations for engagement metrics
    base_queryset = Log.objects.select_related('user__user').annotate(
        reaction_count=Count('reactions', distinct=True),
        comment_count=Count('comments', distinct=True),
    )
    
    if type == 'network':
        # NETWORK FEED: Logs from followed users + secondary network
        
        # Primary network logs (70-80% of feed)
        primary_logs = list(
            base_queryset.filter(user_id__in=primary_network_ids)
            .order_by('-timestamp')[:per_page * 3]  # Fetch extra for scoring
        )
        
        # Secondary network logs (20-30% of feed)
        secondary_network_ids = get_secondary_network_user_ids(user, primary_network_ids)
        secondary_logs = list(
            base_queryset.filter(user_id__in=secondary_network_ids)
            .order_by('-timestamp')[:per_page * 2]
        )
        
        # Score all logs - only secondary network gets recommendation labels
        scored_logs = []
        for log in primary_logs:
            score = calculate_log_score(
                log, user, viewed_log_ids, reacted_log_ids, commented_log_ids,
                is_secondary=False
            )
            log.feed_score = score
            log.feed_type = 'network'
            log.is_secondary_network = False
            log.recommendation_reason = None  # No label for primary network
            scored_logs.append((score, random.random(), log))  # Random for tie-breaking
        
        for log in secondary_logs:
            score = calculate_log_score(
                log, user, viewed_log_ids, reacted_log_ids, commented_log_ids,
                is_secondary=True
            )
            log.feed_score = score
            log.feed_type = 'network'
            log.is_secondary_network = True
            # Add recommendation reason ONLY for secondary network (suggested posts)
            log.recommendation_reason = _get_secondary_recommendation_reason(log, user, primary_network_ids)
            scored_logs.append((score, random.random(), log))
        
        # Sort by score (descending) and get unique logs
        scored_logs.sort(key=lambda x: (-x[0], x[1]))
        
        # DEBUG: Print scores for verification
        print("\n" + "="*60)
        print(f"FEED SCORES FOR USER: {user.user.username}")
        print("="*60)
        for score, _, log in scored_logs:
            network_type = "SECONDARY" if log.is_secondary_network else "PRIMARY"
            print(f"({log.sig} by @{log.user.user.username} [{network_type}]) - Score: {score:.2f}")
        print("="*60 + "\n")
        
        # Deduplicate (same log might appear from multiple paths)
        seen_ids = set()
        unique_logs = []
        for _, _, log in scored_logs:
            if log.id not in seen_ids:
                seen_ids.add(log.id)
                unique_logs.append(log)
        
        logs_list = unique_logs
        
    elif type == 'global':
        # GLOBAL FEED: All logs, globally ranked
        all_logs = list(
            base_queryset.exclude(user=user)
            .order_by('-timestamp')[:per_page * 5]
        )
        
        scored_logs = []
        for log in all_logs:
            score = calculate_log_score(
                log, user, viewed_log_ids, reacted_log_ids, commented_log_ids,
                is_secondary=False
            )
            log.feed_score = score
            log.feed_type = 'global'
            log.is_secondary_network = False
            scored_logs.append((score, random.random(), log))
        
        scored_logs.sort(key=lambda x: (-x[0], x[1]))
        logs_list = [log for _, _, log in scored_logs]
        
    else:
        # LOCAL FEED: For now, same as network (can be extended for location/org)
        primary_logs = list(
            base_queryset.filter(user_id__in=primary_network_ids)
            .order_by('-timestamp')[:per_page * 3]
        )
        
        scored_logs = []
        for log in primary_logs:
            score = calculate_log_score(
                log, user, viewed_log_ids, reacted_log_ids, commented_log_ids,
                is_secondary=False
            )
            log.feed_score = score
            log.feed_type = 'local'
            log.is_secondary_network = False
            scored_logs.append((score, random.random(), log))
        
        scored_logs.sort(key=lambda x: (-x[0], x[1]))
        logs_list = [log for _, _, log in scored_logs]
    
    # Pagination
    paginator = Paginator(logs_list, per_page)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        # Return empty page object
        return paginator.get_page(paginator.num_pages)
    
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