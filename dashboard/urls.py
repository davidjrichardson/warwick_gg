from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='dashboard_index')
]