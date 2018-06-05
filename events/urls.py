from django.urls import path

from events.views import EventView, EventIndexView, SignupFormView, UnsignupFormView, SignupChargeView

urlpatterns = [
    path('', EventIndexView.as_view(), name='event_index'),
    path('<slug:slug>', EventView.as_view(), name='event_home'),
    path('signup/<slug:slug>', SignupFormView.as_view(), name='event_signup'),
    path('signup/charge', SignupChargeView.as_view(), name='event_charge'),
    path('unsignup/<slug:slug>', UnsignupFormView.as_view(), name='event_unsignup'),
]
