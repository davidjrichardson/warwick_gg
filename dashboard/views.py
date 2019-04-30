from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from events.models import Event, Tournament


class DashboardIndexView(LoginRequiredMixin, View):
    template_name = 'dashboard/dashboard_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        next_event = Event.objects.filter(end__gte=timezone.now()).order_by('start').first()
        just_finished = Event.objects.filter(start__lt=timezone.now(),
                                             end__gte=(timezone.now() - timedelta(days=2))).order_by('start').first()
        tournaments = Tournament.objects.filter(start__gte=timezone.now()).order_by('start').all()

        # Clean out the django messages buffer
        _ = list(messages.get_messages(request))
        ctx = {
            'event': next_event,
            'just_finished': just_finished,
            'tournaments': tournaments
        }

        return render(request, self.template_name, ctx)
