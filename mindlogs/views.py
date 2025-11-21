from calendar import month_name
from itertools import islice
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import MindLogForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import MindLog
from .utils import get_24h_mindlog_stats, streak_calculation
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


@login_required
def explore_logs_page(request):
    mindlog_obj = get_24h_mindlog_stats()
    logs_qs = mindlog_obj['logs_qs']
    
    paginator = Paginator(logs_qs, 20)  # 20 logs per page
    page_obj = paginator.page(1)
    
    context = {
        "mindlog_obj": mindlog_obj,
        "logs_qs": page_obj.object_list,
        "has_next": page_obj.has_next(),
    }
    return render(request, "mindlogs/logs.html", context)

#load more option for explore logs
@login_required
def load_more_logs(request):
    page = int(request.GET.get("page", 1))
    logs_qs = MindLog.objects.filter(timestamp__gte=timezone.now() - timedelta(hours=24)).order_by("-timestamp")
    paginator = Paginator(logs_qs, 20)

    try:
        logs_page = paginator.page(page)
    except:
        return JsonResponse({"logs_html": "", "has_next": False})

    html = render_to_string("mindlogs/partials/log_cards.html", {"logs_qs": logs_page.object_list, "user": request.user}, request=request )
    return JsonResponse({
        "logs_html": html,
        "has_next": logs_page.has_next()
    })

@login_required
def terminal_page(request):
    logform = MindLogForm()
    context = {
        'logform': logform,
    }
    return render(request, "mindlogs/log_terminal.html", context)

# for personal log book
@login_required
def personal_logbook(request, username):
    year = int(request.GET.get('year', timezone.now().year))
    try:
        user = User.objects.get(username = username)
    except User.DoesNotExist:
        return render(request, 'mindlogs/logs_user_not_found.html', {"username": username})
        
    info = user.info
    logs = MindLog.objects.filter(user = info).order_by("-timestamp")
    total_logs = logs.count()
    last_log_date = timezone.localtime(logs.first().timestamp).date() if total_logs else None
    
    # Streak calculation
    streak = streak_calculation(logs)
    
    # Clone Impact
    clone_impact = MindLog.objects.filter(original_log__user=info).count()
    
    log_heat_map = logs.filter(
        timestamp__year=year
    ).values_list('timestamp', flat=True)

    log_map = defaultdict(int)
    for ts in log_heat_map:
        date_str = timezone.localtime(ts).strftime('%Y-%m-%d')
        log_map[date_str] += 1

    # Prepare full 1-year grid
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    total_days = (end_date - start_date).days + 1

    contribution_days = []
    for i in range(total_days):
        current_day = start_date + timedelta(days=i)
        contribution_days.append({
            'date': current_day.strftime('%Y-%m-%d'),
            'count': log_map.get(current_day.strftime('%Y-%m-%d'), 0)
        })
        
    contribution_months = build_contribution_months(contribution_days)

    log_year_count =  sum(log_map.values())
    years_available = logs.dates('timestamp', 'year')
    max_streak = get_max_streak(logs)
    
    paginator = Paginator(logs, 20)  # 20 logs per page
    page_obj = paginator.page(1)

    context = {
        "mindlogs": page_obj.object_list,
        'userinfo_obj': info,
        "total_logs": total_logs,
        "last_log_date": last_log_date.strftime("%b %d, %Y") if last_log_date else "—",
        "streak": streak,
        "clone_impact": clone_impact,
        "has_next": page_obj.has_next(),
        
        'log_map': dict(log_map),
        'year': year,
        'years_available': years_available,
        'contribution_months': contribution_months,
        'log_year_count': log_year_count,
        'max_streak': max_streak,
    }
    return render(request, "mindlogs/personal_logbook.html", context)

#load more option for explore logs
@login_required
def load_more_personal_logs(request, username):
    user = get_object_or_404(User, username = username)
    info = user.info
    page = int(request.GET.get("page", 1))
    logs = MindLog.objects.filter(user = info).order_by("-timestamp")
    paginator = Paginator(logs, 20)

    try:
        logs_page = paginator.page(page)
    except:
        return JsonResponse({"logs_html": "", "has_next": False})

    html = render_to_string("mindlogs/partials/personal_log_cards.html", {"mindlogs": logs_page.object_list, "user": request.user}, request=request)
    return JsonResponse({
        "logs_html": html,
        "has_next": logs_page.has_next()
    })

@require_POST
@login_required
def save_mindlog(request):
    if request.method == "POST":
        logform = MindLogForm(request.POST, request.FILES)
        if logform.is_valid():
            log = logform.save(commit=False)
            log.user = request.user.info
            raw_snippet = request.POST.get('code_snippet', '').strip()
            log.code_snippet = raw_snippet[:1000] if raw_snippet else None
            log.link = request.POST.get('link', '').strip()

            log.save()
            
            today = timezone.localtime(timezone.now()).date()
            logs = MindLog.objects.filter(user = request.user.info)
            existing_logs_today = logs.filter(timestamp__date=today).exclude(sig=log.sig).exists() 
            
            if not existing_logs_today:
                streak = streak_calculation(logs)
                request.session['reward_message'] =  f"🔥 {streak} Day Streak!"
                request.session['reward_emojis'] = ['🥳', '🔥']
            else: 
                messages.success(request, "Log committed successfully!")
            return redirect("explore_logs_page")
    return redirect(request.META.get('HTTP_REFERER', '/'))

#save clone log
@login_required
def save_clone_log(request, sig):
    user = request.user.info
    original_log = get_object_or_404(MindLog, sig=sig)
    
    if original_log.user == user:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if original_log.original_log and original_log.original_log.user == user:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    root_log = original_log.original_log if original_log.original_log else original_log
    clone = MindLog.objects.create(
        user=user,
        content=original_log.content,
        original_log=root_log
    )
    root_log.clone_count = root_log.clones.count()
    root_log.save()
    
    today = timezone.localtime(timezone.now()).date()
    logs = MindLog.objects.filter(user = user)
    existing_logs_today = logs.filter(timestamp__date=today).exclude(sig=clone.sig) 
    
    if not existing_logs_today:
        streak = streak_calculation(logs)
        request.session['reward_message'] =  f"🔥 {streak} Day Streak!"
        request.session['reward_emojis'] = ['🥳', '🔥']
    else: 
        messages.success(request, "Log cloned successfully!")
    return redirect(f"{reverse('personal_logbook', args=[request.user.username])}")


@login_required
@require_POST
def delete_log(request, sig):
    userinfo = request.user.info
    try:
        log = MindLog.objects.get(sig=sig)
    except MindLog.DoesNotExist:
        return JsonResponse({'error': 'Log not found'}, status=404)

    if log.user != userinfo:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    log.delete()
    return JsonResponse({'success': True})

def mindbook(request):
    return render(request, "mindlogs/mindbook.html")