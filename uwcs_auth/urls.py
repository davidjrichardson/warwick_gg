from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from uwcs_auth.provider import UWCSProvider

urlpatterns = default_urlpatterns(UWCSProvider)
