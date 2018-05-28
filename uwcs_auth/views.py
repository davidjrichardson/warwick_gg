from itertools import chain

import requests
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from uwcs_auth.forms import UserForm, ProfileForm, DeleteUserForm
from uwcs_auth.models import WarwickGGUser
from uwcs_auth.provider import UWCSProvider

from django.contrib.auth import logout


class UserProfileView(LoginRequiredMixin, View):
    template_name = 'uwcs_auth/me.html'
    login_url = '/accounts/login/'

    def get(self, request):
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=WarwickGGUser.objects.get(user=request.user))

        social_user = SocialAccount.objects.get(user=request.user)

        uni_id = profile_form.instance.uni_id

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'social_account': social_user,
            'uni_id': uni_id,
        }

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=WarwickGGUser.objects.get(user=request.user))

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            ctx = {
                'success': True,
                'values': {
                    'nickname': profile_form.instance.nickname,
                    'first_name': user_form.instance.first_name,
                    'last_name': user_form.instance.last_name,
                    'email': user_form.instance.email
                }
            }
            return JsonResponse(ctx, status=200)
        else:
            errors = dict(chain(user_form.errors.items(), profile_form.errors.items()))
            ctx = {'success': False}
            if errors:
                ctx['errors'] = errors

            return JsonResponse(ctx, status=400)


class UserDeleteView(LoginRequiredMixin, View):
    template_name = 'uwcs_auth/delete_account.html'
    login_url = '/accounts/login/'

    def get(self, request):
        user_form = DeleteUserForm(instance=request.user)

        ctx = {
            'user_form': user_form
        }

        return render(request, self.template_name, context=ctx)

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        user_form = DeleteUserForm(request.POST, instance=request.user)

        if user_form.is_valid():
            user = request.user
            logout(request)
            user.delete()

            return redirect('/')


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
