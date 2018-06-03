from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from django.urls import path

from uwcs_auth import views
from uwcs_auth.provider import UWCSProvider

urlpatterns = default_urlpatterns(UWCSProvider)

urlpatterns = urlpatterns + [
    path('me/', views.UserProfileView.as_view(), name='user_profile'),
    path('delete/', views.UserDeleteView.as_view(), name='account_delete'),
]