from django.shortcuts import render, get_object_or_404, redirect
from django.views import View

from events.models import Event


class HomePageView(View):
    template_name = 'home.html'

    def get(self, request):
        return render(request, self.template_name)


class PrivacyPolicyView(View):
    template_name = 'privacy_policy.html'

    def get(self, request):
        return render(request, self.template_name)


class EventSlugRedirectView(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        return redirect(event)
