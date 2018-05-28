import requests
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from uwcs_auth.forms import UserForm, ProfileForm
from uwcs_auth.models import WarwickGGUser
from uwcs_auth.provider import UWCSProvider


class UserProfileView(LoginRequiredMixin, View):
    template_name = 'uwcs_auth/me.html'
    login_url = '/accounts/login/'

    def get(self, request):
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=WarwickGGUser.objects.get(user=request.user))

        social_user = SocialAccount.objects.get(user=request.user)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'social_account': social_user,
        }

        return render(request, self.template_name, context=context)


class UserDeleteView(LoginRequiredMixin, View):
    template_name = 'uwcs_auth/delete_account.html'
    login_url = '/accounts/login/'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        pass


class UWCSOauth2Adapter(OAuth2Adapter):
    provider_id = UWCSProvider.id
    access_token_url = 'https://uwcs.co.uk/o/token/'
    authorize_url = 'https://uwcs.co.uk/o/authorize/'
    profile_url = 'https://uwcs.co.uk/api/me'

    def complete_login(self, request, app, access_token, **kwargs):
        headers = {
            'Authorization': 'Bearer {0}'.format(access_token.token),
            'Content-Type': 'application/json',
        }
        extra_data = requests.get(self.profile_url, headers=headers)

        return self.get_provider().sociallogin_from_response(request, extra_data.json())


oauth2_login = OAuth2LoginView.adapter_view(UWCSOauth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UWCSOauth2Adapter)
