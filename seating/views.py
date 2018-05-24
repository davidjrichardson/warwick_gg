from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class SeatingIndexView(View, LoginRequiredMixin):
    template_name = 'seating/seating_index.html'

    def get(self, request):
        return render(request, self.template_name)
