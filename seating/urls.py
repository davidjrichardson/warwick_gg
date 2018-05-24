from django.urls import path

from . import views

urlpatterns = [
    path('', views.SeatingIndexView.as_view(), name='seating_index')
]
