import random

from django import forms
from django.forms import Widget

from events.models import EventSignup

PLACEHOLDER_TEXTS = [
    'Bottom text',
    'First!!!11',
    '🚅🚅🚅',
    'Thanks for another £5 donation to RNJesus',
    'MOOP VEEN',
    'According to all known laws of aviation, there is no way that a bee should be able to fly. Its wings are too small to get its fat little body off the ground.'
]


def get_placeholder():
    return PLACEHOLDER_TEXTS[int(random.random() * len(PLACEHOLDER_TEXTS))]


class Textarea(Widget):
    input_type = 'textarea'
    template_name = 'django/forms/widgets/textarea.html'

    def __init__(self, attrs=None):
        # Use slightly better defaults than HTML's 20x2 box
        default_attrs = {'cols': '40', 'rows': '10'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class SignupForm(forms.ModelForm):
    class Meta:
        model = EventSignup
        fields = ['comment']
        widgets = {
            'comment': Textarea(attrs={
                'placeholder': get_placeholder(),
            })
        }
