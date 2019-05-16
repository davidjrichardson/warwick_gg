from django.urls import path

from events.views import EventView, EventIndexView, SignupFormView, UnsignupFormView, SignupChargeView, \
    UnsignupConfirmView, DeleteCommentView, TournamentIndexView, TournamentView, StripeWebhookView, UpdateCommentView, \
    TournamentSignupView, TournamentUnsignupView, TournamentSignupConfirmView, TournamentUnsignupConfirmView

urlpatterns = [
    path('', EventIndexView.as_view(), name='event_index'),
    path('verify', StripeWebhookView.as_view(), name='stripe_webhook_endpoint'),
    path('tournaments', TournamentIndexView.as_view(), name='tournament_index'),
    path('tournaments/<slug:slug>', TournamentView.as_view(), name='tournament_home'),
    path('tournaments/signup/<slug:slug>', TournamentSignupView.as_view(), name='tournament_signup'),
    path('tournaments/signup/confirm', TournamentSignupConfirmView.as_view(), name='tournament_signup'),
    path('tournaments/unsignup/<slug:slug>', TournamentUnsignupView.as_view(), name='tournament_unsignup'),
    path('tournaments/unsignup/confirm', TournamentUnsignupConfirmView.as_view(), name='tournament_unsignup'),
    path('<slug:slug>', EventView.as_view(), name='event_home'),
    path('signup/confirm', SignupChargeView.as_view(), name='event_charge'),
    path('signup/<slug:slug>', SignupFormView.as_view(), name='event_signup'),
    path('unsignup/confirm', UnsignupConfirmView.as_view(), name='event_unsignup_confirm'),
    path('unsignup/<slug:slug>', UnsignupFormView.as_view(), name='event_unsignup'),
    path('api/comment/update', UpdateCommentView.as_view(), name='update_comment'),
    path('api/comment/delete', DeleteCommentView.as_view(), name='delete_comment'),
]
