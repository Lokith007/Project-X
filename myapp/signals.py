from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_in
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, pre_save
from myapp.models import userinfo, education 
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import userinfo, education

@receiver(post_save, sender=User)
def create_related_user_models(sender, instance, created, **kwargs):
    if created:
        info, _ = userinfo.objects.get_or_create(user=instance)
        education.objects.get_or_create(user=info)
        
@receiver(user_signed_up)
def handle_new_social_signup(request, user, **kwargs):
    if hasattr(user, 'info'):
        user.info.needs_profile_completion = True
        user.info.save()

@receiver(pre_save, sender=userinfo)
def delete_old_userinfo_profile_image(sender, instance, **kwargs):
    if not instance.pk:  # If this is a new instance, skip
        return
    
    try:
        old_instance = userinfo.objects.only('profile_image').get(pk=instance.pk)
    except userinfo.DoesNotExist:
        return
    
    # Skip if old profile_image is empty or the default
    if (old_instance.profile_image and old_instance.profile_image.name and 
        old_instance.profile_image != instance.profile_image and 
        old_instance.profile_image.name != old_instance.profile_image.field.default and 
        default_storage.exists(old_instance.profile_image.name)):
        default_storage.delete(old_instance.profile_image.name)
        
@receiver(post_delete, sender=userinfo)
def delete_userinfo_profile_image_on_delete(sender, instance, **kwargs):
    # Skip if profile_image is empty or the default
    if (instance.profile_image and instance.profile_image.name and 
        instance.profile_image.name != instance.profile_image.field.default):
        if default_storage.exists(instance.profile_image.name):
            default_storage.delete(instance.profile_image.name)
            