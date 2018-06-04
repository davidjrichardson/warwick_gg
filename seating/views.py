from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
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
    template_name = 'seating/seating_page.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        # Check if the user has signed up
        has_signed_up = EventSignup.objects.for_event(event, request.user).exists()
        # Check if the user is an exec member
        is_exec = 'exec' in request.user.groups.values_list(Lower('name'), flat=True)

        print(is_exec, 'signup', has_signed_up)

        ctx = {
            'event': event,
            'has_signed_up': has_signed_up,
            'is_exec': is_exec,
            'slug': slug,
        }
        return render(request, self.template_name, context=ctx)
