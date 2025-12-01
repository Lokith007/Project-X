"""
Developer Search Utility
Provides fuzzy search with intelligent ranking based on search relevance and network proximity
"""
from django.db.models import Q, Count, Case, When, IntegerField, Value
from django.contrib.postgres.search import TrigramSimilarity
from myapp.models import userinfo
import re


def search_developers(query, current_user, limit=20):
    """
    Search developers with fuzzy matching and network-aware ranking
    
    Args:
        query: Search string
        current_user: User object performing the search
        limit: Maximum number of results to return
    
    Returns:
        List of tuples: [(userinfo_obj, final_score, mutual_count), ...]
        Sorted by final_score descending
    """
    # Get current user's userinfo
    if hasattr(current_user, 'info'):
        current_userinfo = current_user.info
    else:
        current_userinfo = current_user
    
    # Sanitize query
    query = sanitize_query(query)
    
    if not query or len(query) < 2:
        return []
    
    # Get user's following for mutual connection calculation
    current_following = set(current_userinfo.following.values_list('following_id', flat=True))
    
    # Perform fuzzy search using trigram similarity
    candidates = userinfo.objects.exclude(
        id=current_userinfo.id  # Exclude self
    ).select_related(
        'user',
        'coding_style'
    ).prefetch_related(
        'following__following'
    ).annotate(
        # Trigram similarity for username
        username_sim=TrigramSimilarity('user__username', query),
        # Trigram similarity for first name
        first_name_sim=TrigramSimilarity('user__first_name', query),
        # Trigram similarity for last name
        last_name_sim=TrigramSimilarity('user__last_name', query),
        # Trigram similarity for bio
        bio_sim=TrigramSimilarity('bio', query),
    ).filter(
        Q(username_sim__gt=0.1) |
        Q(first_name_sim__gt=0.1) |
        Q(last_name_sim__gt=0.1) |
        Q(bio_sim__gt=0.1) |
        Q(user__username__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(bio__icontains=query)
    )[:100]  # Limit initial candidates for performance
    
    # Score and rank results
    scored_results = []
    
    for candidate in candidates:
        # Calculate search relevance score (0-100)
        search_score = calculate_search_relevance(
            candidate, query,
            candidate.username_sim,
            candidate.first_name_sim,
            candidate.last_name_sim,
            candidate.bio_sim
        )
        
        # Calculate network score (0-100)
        mutual_count = calculate_mutual_connections(candidate, current_following)
        network_score = calculate_network_score(candidate, current_userinfo, mutual_count)
        
        # Composite score: 60% search relevance + 40% network score
        final_score = (search_score * 0.6) + (network_score * 0.4)
        
        scored_results.append((candidate, final_score, mutual_count))
    
    # Sort by final score descending
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results[:limit]


def sanitize_query(query):
    """Remove special characters and normalize query"""
    if not query:
        return ""
    
    # Remove special characters except @, ., -, and spaces
    query = re.sub(r'[^\w\s@.-]', '', query)
    
    # Normalize whitespace
    query = ' '.join(query.split())
    
    return query.strip()


def calculate_search_relevance(candidate, query, username_sim, first_name_sim, last_name_sim, bio_sim):
    """
    Calculate search relevance score (0-100)
    
    Weights:
    - Username: 40%
    - Full name: 30%
    - Bio: 15%
    - Skills: 10%
    - Location: 5%
    """
    score = 0
    query_lower = query.lower()
    
    # Username matching (40 points max)
    username = candidate.user.username.lower()
    if username == query_lower:
        score += 40  # Exact match
    elif username.startswith(query_lower):
        score += 35  # Prefix match
    elif query_lower in username:
        score += 30  # Contains match
    else:
        # Fuzzy match using trigram similarity
        score += username_sim * 40
    
    # Full name matching (30 points max)
    full_name = f"{candidate.user.first_name} {candidate.user.last_name}".lower()
    if full_name == query_lower:
        score += 30  # Exact match
    elif query_lower in full_name:
        score += 25  # Contains match
    else:
        # Fuzzy match using trigram similarity
        name_sim = max(first_name_sim, last_name_sim)
        score += name_sim * 30
    
    # Bio matching (15 points max)
    if candidate.bio:
        bio_lower = candidate.bio.lower()
        if query_lower in bio_lower:
            score += 15
        else:
            score += bio_sim * 15
    
    # Skills matching (10 points max)
    skills = candidate.skills.all()
    skill_names = [s.name.lower() for s in skills]
    if any(query_lower in skill for skill in skill_names):
        score += 10
    elif any(query_lower == skill for skill in skill_names):
        score += 10
    
    # Location matching (5 points max)
    if candidate.city and query_lower in candidate.city.lower():
        score += 5
    elif candidate.location and query_lower in candidate.location.lower():
        score += 3
    
    return min(score, 100)


def calculate_mutual_connections(candidate, current_following):
    """Calculate number of mutual connections"""
    candidate_following = set(candidate.following.values_list('following_id', flat=True))
    mutual = current_following & candidate_following
    return len(mutual)


def calculate_network_score(candidate, current_user, mutual_count):
    """
    Calculate network proximity score (0-100)
    
    Factors:
    - Mutual connections (primary)
    - Shared coding style
    - Same location
    """
    score = 0
    
    # Mutual connections (up to 100 points)
    # 10 points per mutual, capped at 100
    score += min(mutual_count * 10, 100)
    
    # Shared coding style bonus (+10)
    if candidate.coding_style and current_user.coding_style:
        if candidate.coding_style == current_user.coding_style:
            score += 10
    
    # Same location bonus (+5)
    if candidate.city and current_user.city:
        if candidate.city == current_user.city:
            score += 5
    
    return min(score, 100)
