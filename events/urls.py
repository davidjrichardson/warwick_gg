from django.urls import path

from events.views import EventView, EventIndexView

urlpatterns = [
    path('', EventIndexView.as_view(), name='event_index'),
    path('<slug:slug>', EventView.as_view(), name='event_home'),
]
