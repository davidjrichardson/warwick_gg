from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View

from events.models import Event, EventSignup


class SeatingFAQView(LoginRequiredMixin, View):
    template_name = 'seating/seating_faq.html'
    login_url = '/accounts/login/'

    def get(self, request):
        ctx = {}
        return render(request, self.template_name, context=ctx)


class SeatingView(LoginRequiredMixin, View):
    template_name = 'seating/seating_index.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = False
        if request.user.is_authenticated:
            signup = EventSignup.objects.for_event(event, request.user).first()

            # If the user hasn't signed up
            if signup:
                has_signed_up = True

            # if has_signed_up:
            ctx = {
                'event': event,
            }
            return render(request, self.template_name, context=ctx)
        # else:
        #     TODO: Redirect with message that the user needs to sign up
        # return redirect('event_home', slug=slug)
