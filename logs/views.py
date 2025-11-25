from calendar import month_name
from itertools import islice
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import LogForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Log
from .utils import get_24h_log_stats, streak_calculation
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from collections import Counter, defaultdict
from datetime import date, timedelta
from django.db.models import Avg
from django.contrib import messages

def chunk_list(data, size):
    it = iter(data)
    return list(iter(lambda: list(islice(it, size)), []))

def build_contribution_months(contribution_days):
    months = [[] for _ in range(12)]  # 0 to 11 months

    for day in contribution_days:
        month_index = int(day['date'][5:7]) - 1  # Extract MM from YYYY-MM-DD
        months[month_index].append(day)

    # Now chunk each month into weeks of 7 days
    contribution_months = []
    for idx, days in enumerate(months):
        weeks = chunk_list(days, 7)
        contribution_months.append((month_name[idx+1], weeks))

    return contribution_months

def get_max_streak(logs_queryset):
    """Returns the maximum streak (longest consecutive-day logging streak)."""
    # Get unique dates only, sorted
    log_dates = sorted(set(log.timestamp.date() for log in logs_queryset))

    max_streak = 0
    current_streak = 1

    for i in range(1, len(log_dates)):
        if log_dates[i] == log_dates[i-1] + timedelta(days=1):
            current_streak += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1

    max_streak = max(max_streak, current_streak) if log_dates else 0
    return max_streak


def load_more_profile_logs(request, username):
    """
    Cursor-based pagination for loading more logs on user profile.
    Uses timestamp cursor for efficient pagination.
    """
    user = get_object_or_404(User, username=username)
    info = user.info
    
    # Get cursor (last log timestamp) from request
    cursor = request.GET.get("cursor")
    per_page = 10  # Load 10 logs at a time
    
    # Build query
    logs_query = Log.objects.filter(user=info).order_by("-timestamp")
    
    # Apply cursor filter if provided
    if cursor:
        try:
            cursor_datetime = timezone.datetime.fromisoformat(cursor)
            logs_query = logs_query.filter(timestamp__lt=cursor_datetime)
        except (ValueError, TypeError):
            pass  # Invalid cursor, just ignore it
    
    # Fetch one extra to check if there are more
    logs = list(logs_query[:per_page + 1])
    
    has_next = len(logs) > per_page
    if has_next:
        logs = logs[:per_page]  # Remove the extra one
    
    # Get new cursor (timestamp of last log)
    new_cursor = logs[-1].timestamp.isoformat() if logs else None
    
    # Render HTML
    html = render_to_string(
        "logs/partials/personal_log_cards.html",
        {"logs": logs, "user": request.user},
        request=request
    )
    
    return JsonResponse({
        "logs_html": html,
        "has_next": has_next,
        "cursor": new_cursor
    })


@require_POST
@login_required
def save_log(request):
    if request.method == "POST":
        logform = LogForm(request.POST, request.FILES)
        if logform.is_valid():
            log = logform.save(commit=False)
            log.user = request.user.info
            raw_snippet = request.POST.get('code_snippet', '').strip()
            log.code_snippet = raw_snippet[:5000] if raw_snippet else None
            log.link = request.POST.get('link', '').strip()

            log.save()
            
            today = timezone.localtime(timezone.now()).date()
            logs = Log.objects.filter(user = request.user.info)
            existing_logs_today = logs.filter(timestamp__date=today).exclude(sig=log.sig).exists() 
            
            if not existing_logs_today:
                streak = streak_calculation(logs)
                request.session['reward_message'] =  f"🔥 {streak} Day Streak!"
                request.session['reward_emojis'] = ['🥳', '🔥']
            else: 
                messages.success(request, "Log committed successfully!")
            return redirect("index")
    return redirect(request.META.get('HTTP_REFERER', '/'))

#save clone log
@login_required
def save_clone_log(request, sig):
    user = request.user.info
    original_log = get_object_or_404(Log, sig=sig)
    
    if original_log.user == user:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if original_log.original_log and original_log.original_log.user == user:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    root_log = original_log.original_log if original_log.original_log else original_log
    clone = Log.objects.create(
        user=user,
        content=original_log.content,
        original_log=root_log
    )
    root_log.clone_count = root_log.clones.count()
    root_log.save()
    
    today = timezone.localtime(timezone.now()).date()
    logs = Log.objects.filter(user = user)
    existing_logs_today = logs.filter(timestamp__date=today).exclude(sig=clone.sig) 
    
    if not existing_logs_today:
        streak = streak_calculation(logs)
        request.session['reward_message'] =  f"🔥 {streak} Day Streak!"
        request.session['reward_emojis'] = ['🥳', '🔥']
    else: 
        messages.success(request, "Log cloned successfully!")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def delete_log(request, sig):
    userinfo = request.user.info
    try:
        log = Log.objects.get(sig=sig)
    except Log.DoesNotExist:
        return JsonResponse({'error': 'Log not found'}, status=404)

    if log.user != userinfo:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    log.delete()
    return JsonResponse({'success': True})
