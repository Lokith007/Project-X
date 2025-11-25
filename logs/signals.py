from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage

from .models import Log

@receiver(post_delete, sender=Log)
def delete_log_snapshot(sender, instance, **kwargs):
    if instance.snap_shot and instance.snap_shot.name:
        if default_storage.exists(instance.snap_shot.name):
            default_storage.delete(instance.snap_shot.name)