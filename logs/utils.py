from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .models import Log
import math

def get_24h_log_stats():
    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    logs_qs = Log.objects.filter(timestamp__gte=last_24h).order_by("-timestamp")
    
    stats = {
        "logs_qs": logs_qs,
        "logs_fired": logs_qs.count(),
        "logs_per_min": math.ceil(logs_qs.count() / (24 * 60)),
        "clones_today": logs_qs.filter(original_log__isnull=False).count(),
    }
    return stats

def streak_calculation(logs):
    today = timezone.now().date()
    streak = 0
    seen_days = set(log.timestamp.date() for log in logs)
    missed_day = False

    for i in range(0, 365):
        day = today - timedelta(days=i)
        if day in seen_days:
            streak += 1
        elif day == today:
            # Allow current day to not break streak
            continue
        else:
            missed_day = True
            break
    return streak


