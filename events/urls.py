from django.urls import path

from events.views import EventView, EventIndexView, SignupFormView, UnsignupFormView, SignupChargeView, \
    UnsignupConfirmView, DeleteCommentView

urlpatterns = [
    path('', EventIndexView.as_view(), name='event_index'),
    path('<slug:slug>', EventView.as_view(), name='event_home'),
    path('signup/confirm', SignupChargeView.as_view(), name='event_charge'),
    path('signup/<slug:slug>', SignupFormView.as_view(), name='event_signup'),
    path('unsignup/confirm', UnsignupConfirmView.as_view(), name='event_unsignup_confirm'),
    path('unsignup/<slug:slug>', UnsignupFormView.as_view(), name='event_unsignup'),
    path('api/comment/delete', DeleteCommentView.as_view(), name='delete_comment'),
]
