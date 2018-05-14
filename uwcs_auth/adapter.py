from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from uwcs_auth.models import WarwickGGUser


class WarwickGGUserAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Add the first and last names to the user
        user = super(WarwickGGUserAccountAdapter, self).save_user(request, user, form, commit=False)
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.save()

        # Create the associated profile model
        user_profile = WarwickGGUser(user=user, uni_id=form.cleaned_data.get('uni_id'),
                                     nickname=form.cleaned_data.get('nickname'))
        user_profile.save()


class UWCSUserAccountAdapter(DefaultSocialAccountAdapter):

    def get_signup_form_initial_data(self, sociallogin):
        user = sociallogin.user

        initial = {
            'email': user_email(user) or '',
            'uni_id': sociallogin.account.extra_data.get('user').get('username') or '',
            'nickname': sociallogin.account.extra_data.get('nickname') or '',
            'first_name': user_field(user, 'first_name') or '',
            'last_name': user_field(user, 'last_name') or ''}

        return initial

    def save_user(self, request, sociallogin, form=None):
        user = super(UWCSUserAccountAdapter, self).save_user(request, sociallogin, form)

        initial = self.get_signup_form_initial_data(sociallogin)

        # Create the associated profile model
        user_profile = WarwickGGUser(user=user, uni_id=initial.get('uni_id'),
                                     nickname=initial.get('nickname'))
        user_profile.save()
