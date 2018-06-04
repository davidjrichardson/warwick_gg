from django.urls import path

from seating.views import SeatingView, SeatingFAQView

urlpatterns = [
    path('<slug:slug>', SeatingView.as_view(), name='event_seating'),
    path('faqs/', SeatingFAQView.as_view(), name='seating_faqs'),
]
