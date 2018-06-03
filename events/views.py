from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View

from events.models import Event, EventSignup


class EventIndexView(LoginRequiredMixin, View):
    template_name = 'events/event_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        ctx = {}
        return render(request, self.template_name, context=ctx)


class EventView(View):
    template_name = 'events/event_home.html'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = False

        if request.user.is_authenticated:
            signup = EventSignup.objects.for_event(event, request.user).first()

            # If the user hasn't signed up
            if signup:
                has_signed_up = True

        ctx = {
            'event': event,
            'has_signed_up': has_signed_up,
            'event_slug': slug,
        }

        return render(request, self.template_name, context=ctx)


class SignupFormView(LoginRequiredMixin, View):
    template_name = 'events/signup_view.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        ctx = {}
        return render(request, self.template_name, context=ctx)


class UnsignupFormView(LoginRequiredMixin, View):
    template_name = 'events/unsignup_view.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        ctx = {}
        return render(request, self.template_name, context=ctx)
