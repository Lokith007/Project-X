from django.urls import path
from . import views

urlpatterns = [
    path("", views.explore_logs_page, name="explore_logs_page"),
    path("terminal/", views.terminal_page, name='terminal_page'),
    path("logbook/<str:username>/", views.personal_logbook, name="personal_logbook"),
    path("mindbook/", views.mindbook, name='mind_book' ),
    
    path("save-log/", views.save_mindlog, name="save_mindlog"),
    path('save-clone-log/<str:sig>/', views.save_clone_log, name='save_clone_log'),
    path("delete-log/<str:sig>/", views.delete_log, name="delete_log"),
    
    path("load-more/", views.load_more_logs, name="load_more_logs"),
    path("personal-load-more/<str:username>/", views.load_more_personal_logs, name="load_more_personal_logs"),
]
