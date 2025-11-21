from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("contribute/", views.contribute_page, name="contribute_page"),
    path("feedback/", views.feedback_page, name="feedback_page"),
    path("post-login-check/", views.post_login_check, name=""),
    
    # path("sign-up/", views.sign_up.as_view(), name="sign_up"),
    path("aboutuser/<uuid:uuid>", views.signup_about , name="signup_about"),
    path("character/<uuid:uuid>", views.signup_character, name="signup_character"),
    path("skills/<uuid:uuid>", views.signup_skills, name="signup_skills"),
    path("", views.home_page, name="index"),
    path('load-more-feed/', views.load_more_feed, name='load_more_feed'),
    path("notification/", views.notification_page, name="notification_page"),
    path('notifications/count/', views.get_notification_count, name='get_notification_count'),
    
    path("explore-dev/", views.explore_dev, name="explore_dev"),
    path("explore-projects/", views.explore_project, name="explore-project"),
    path("explore-organization/", views.explore_organization, name="explore_organization"),
    path("explore-events/", views.explore_events, name="explore_events"),
    
    # User-profile
    path("user-profile/<str:user_name>/", views.user_profile, name="user_profile"),
    path("<str:username>/user-follow-list/", views.follow_list, name="follow_list"),
    path("unfollow/<int:otheruserinfo_id>/", views.unfollow_user, name = 'unfollow_user'),
    path("follow/<int:otheruserinfo_id>/", views.follow_user, name = 'follow_user'),
    path('saved', views.saved_page, name = 'saved_page'),

    path("create-org/", views.create_organization, name="create_organization"),
    path("manage-org/", views.manage_organization, name="manage_organization"),
    path("organization/<int:id>/", views.organization_detail, name="organization_detail"),
    path("<int:org_id>/org-follow-list/", views.org_follow_list, name="org_follow_list"),
    path('organization/<int:organization_id>/follow/', views.follow_organization, name='follow_organization'),
    path('organization/<int:organization_id>/unfollow/', views.unfollow_organization, name='unfollow_organization'),
    
    path('toggle_like/<int:post_id>/', views.toggle_like, name = 'toggle_like'),
    path("toggle_post_save/<int:post_id>/", views.toggle_post_save, name="toggle_post_save"),
    path("save-post/", views.save_post, name="save_post"),
    path("delete-post/<int:post_id>/", views.delete_post, name="delete_post"),
    path("save-comment/", views.save_comment, name="save_comment"),
    path('delete-post-comment/<int:comment_id>/', views.delete_post_comment, name='delete_post_comment'),
    
    path("calendar/", views.calendar_page, name="calendar_page"),
    path("settings/", views.settings_page, name="settings_page"),
    path('delete-data/', views.delete_data, name = 'delete_data'),
    
    path("delete_account/<uuid:uuid>/", views.delete_account, name="delete_acount")
]