from django.db import models
from django.urls import reverse
import uuid
from .users import userinfo
from .filter import Domain, skill
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.timezone import now


# User-Posts
class post(models.Model):
    ASPECT_CHOICES = [
        ('Original', 'Original'),
        ('1:1', '1:1'),
        ('16:9', '16:9'),
    ]
    content = models.TextField()
    file = models.ImageField(upload_to='user-posts', null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(userinfo, related_name='liked_posts', blank=True)
    aspect = models.CharField(max_length=10, choices=ASPECT_CHOICES, default='16:9')
    
    # Either a User OR an Organization can be the author
    user = models.ForeignKey(userinfo, related_name='all_post', on_delete=models.CASCADE, null=True, blank=True)

    # post_type = models.CharField(max_length=10, choices=POST_TYPE, default='img')
    def __str__(self):
        return f"{self.id} Post by {self.user or self.Organization}"
    
    def total_likes(self):
        return self.likes.count()
    
    def tot_comments(self):
        return self.comments.count()
    
class post_comments(models.Model):
    user = models.ForeignKey(userinfo, related_name='post_comments', on_delete=models.CASCADE)
    Post = models.ForeignKey(post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Comment by {self.user} on {self.Post.id}"
    
    class Meta:
        verbose_name_plural = "Post comments"
        ordering = ['-created_at']  
    
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Liked your post'),
        ('comment', 'Commented on your post'),
        ('follow', 'Started following you'),
    )
    user = models.ForeignKey(userinfo, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(userinfo, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(choices=NOTIFICATION_TYPES, max_length=60)
    post = models.ForeignKey(post, on_delete=models.CASCADE, null=True, blank=True)
    post_comment = models.ForeignKey(post_comments, on_delete=models.CASCADE, null=True, blank=True) 
  
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    def __str__(self):
        return f"{self.id} {self.sender} {self.get_notification_type_display()} {self.user}"
    