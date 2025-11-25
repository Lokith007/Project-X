"""
URL configuration for DevMate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from myapp.views import CustomPasswordChangeView, logout_view

urlpatterns = [
    path('admin/', include('admin_honeypot.urls')),
    path("admin-project-x/", admin.site.urls),
    path('select2/', include('django_select2.urls')),
    # path("", include('django.contrib.auth.urls'), name=""),
    # path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),  # Specific redirect
    # path("accounts/signup/", RedirectView.as_view(url='/sign-up', perman{% url 'logout' %}ent=True)),
    path('accounts/password/change/', CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('accounts/logout/', logout_view, name='account_logout'),
    path('accounts/', include('allauth.urls')),
    path("tinymce/", include('tinymce.urls')),
    path("logs/", include("logs.urls")),
    path('', include('myapp.urls')),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
