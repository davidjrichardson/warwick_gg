from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class DashboardIndexView(View, LoginRequiredMixin):
    template_name = 'dashboard/dashboard_index.html'

    def get(self, request):
        return render(request, self.template_name)
