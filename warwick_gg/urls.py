"""warwick_gg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from warwick_gg.views import HomePageView, EventSlugRedirectView, PrivacyPolicyView, AboutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('privacy', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('about', AboutView.as_view(), name='about'),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('allauth.urls')),
    path('avatar/', include('avatar.urls')),
    path('admin/', admin.site.urls),
    path('events/', include('events.urls')),

    path('seating/', include('seating.urls')),
  
    # Event slug short url redirect
    path('<slug:slug>/', EventSlugRedirectView.as_view()),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
