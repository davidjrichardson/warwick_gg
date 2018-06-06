from django.urls import path

from seating.views import SeatingView, SeatingFAQView, SeatingRoomAPIView, SeatingRoomRevisionListAPIView, \
    SeatingRoomAPISubmitRevisionView

urlpatterns = [
    path('<slug:slug>', SeatingView.as_view(), name='event_seating'),
    path('faqs/', SeatingFAQView.as_view(), name='seating_faqs'),
    path('api/seats/<int:event_id>', SeatingRoomAPIView.as_view(), name='seating_api'),
    path('api/revisions/<int:event_id>', SeatingRoomRevisionListAPIView.as_view(), name='seating_revision_api'),
    path('api/submit/<int:event_id>', SeatingRoomAPISubmitRevisionView.as_view(), name='seating_submit_api'),
]
