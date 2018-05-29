from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View

from events.models import Event


class HomePageView(View):
    template_name = 'home.html'

    def get(self, request):
        ctx = {
            'has_launched': settings.HAS_LAUNCHED
        }

        return render(request, self.template_name, context=ctx)


class EventSlugRedirectView(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        return redirect(event)
