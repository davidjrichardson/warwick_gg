from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View

from events.models import Event


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

        ctx = {
            'event': event
        }

        return render(request, self.template_name, context=ctx)
