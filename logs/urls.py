from django.urls import path
from . import views

urlpatterns = [
    path("", views.explore_logs_page, name="explore_logs_page"),
    
    path("logbook/<str:username>/", views.personal_logbook, name="personal_logbook"),

    
    path("save-log/", views.save_log, name="save_log"),
    path('save-clone-log/<str:sig>/', views.save_clone_log, name='save_clone_log'),
    path("delete-log/<str:sig>/", views.delete_log, name="delete_log"),
    
    path("load-more/", views.load_more_logs, name="load_more_logs"),
    path("personal-load-more/<str:username>/", views.load_more_personal_logs, name="load_more_personal_logs"),
]
