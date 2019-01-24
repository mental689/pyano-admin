"""pyano_admin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf.urls import url

if 'pinax.notifications' in settings.INSTALLED_APPS:
    from pinax.notifications import models as notification
    from vatic.views import VATICJobNoticeSettingsView
else:
    notification = None

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employer.urls')),
    path('worker/', include('worker.urls')),
    path('vatic/', include('vatic.urls')),
    path('search/', include('search.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^survey/', include('survey.urls')),
    url(r'^comments/', include('django_comments_xtd.urls')),
    url(r'^avatar/', include('avatar.urls')),
    #url(r"^notifications/", include("pinax.notifications.urls", namespace="pinax_notifications")),
]

if notification:
    urlpatterns.extend([
        url(r"^notifications/settings/$", VATICJobNoticeSettingsView.as_view(), name="notification_notice_settings"),
    ])
