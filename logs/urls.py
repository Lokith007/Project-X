from django.urls import path
from . import views

urlpatterns = [
    path("save-log/", views.save_log, name="save_log"),
    path('save-clone-log/<str:sig>/', views.save_clone_log, name='save_clone_log'),
    path("delete-log/<str:sig>/", views.delete_log, name="delete_log"),
    
    path("load-more-profile-logs/<str:username>/", views.load_more_profile_logs, name="load_more_profile_logs"),
]
