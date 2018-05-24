from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class DashboardIndexView(LoginRequiredMixin, View):
    template_name = 'dashboard/dashboard_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        return render(request, self.template_name)
