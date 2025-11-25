from django.db import models
from django.urls import reverse
import uuid
from .users import userinfo
from .filter import Domain, skill
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.timezone import now


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('follow', 'Started following you'),
    )
    user = models.ForeignKey(userinfo, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(userinfo, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(choices=NOTIFICATION_TYPES, max_length=60)
  
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    def __str__(self):
        return f"{self.id} {self.sender} {self.get_notification_type_display()} {self.user}"
    