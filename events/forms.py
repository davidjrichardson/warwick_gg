from django import forms

from events.models import EventSignup


class SignupForm(forms.ModelForm):
    class Meta:
        model = EventSignup
        fields = ['comment', 'photography_consent']
