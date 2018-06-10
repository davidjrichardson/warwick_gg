import xml.etree.ElementTree as ET

import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.functions import Lower
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from stripe import Charge, StripeError, Refund

from events.forms import SignupForm
from events.models import Event, EventSignup, Tournament
from seating.models import Seating
from uwcs_auth.models import WarwickGGUser


class EventIndexView(LoginRequiredMixin, View):
    template_name = 'events/event_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        ctx = {
            'events': Event.objects.filter(end__gte=timezone.now()).order_by('start').all()
        }
        return render(request, self.template_name, context=ctx)


class EventView(View):
    template_name = 'events/event_home.html'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = False
        if request.user.is_authenticated:
            has_signed_up = EventSignup.objects.for_event(event, request.user).exists()

        if has_signed_up:
            signups = event.signups
        else:
            signups = []

        ctx = {
            'event': event,
            'has_signed_up': has_signed_up,
            'signups_open': event.signups_open(request.user),
            'signup_start': event.signup_start_for_user(request.user),
            'signups_remaining': event.signup_limit - event.signup_count,
            'signups': signups,
            'tournaments': Tournament.objects.for_event(event),
            'is_exec': WarwickGGUser.objects.get(user=request.user).is_exec if request.user.is_authenticated else False
        }

        return render(request, self.template_name, context=ctx)


class TournamentView(View):
    template_name = 'tournaments/tournament_home.html'

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)
        tournament_event = Event.objects.get(id=tournament.for_event.id) if tournament.for_event else None

        ctx = {
            'tournament': tournament,
            'tournament_event': tournament_event,
        }
        return render(request, self.template_name, context=ctx)


class TournamentIndexView(LoginRequiredMixin, View):
    template_name = 'tournaments/tournament_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        tournaments = Tournament.objects.filter(start__gte=timezone.now()).order_by('start').all()

        ctx = {
            'tournaments': tournaments
        }
        return render(request, self.template_name, context=ctx)


class DeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = '/accounts/login/'

    def test_func(self):
        return 'exec' in self.request.user.groups.values_list(Lower('name'), flat=True)

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('comment-id'):
            return HttpResponseBadRequest()

        signup = get_object_or_404(EventSignup, id=request.POST.get('comment-id'))
        signup.comment = None
        signup.save()

        return HttpResponse()


def check_membership(api_token, profile, request, society):
    if society == 'UWCS':
        return SocialAccount.objects.filter(user=profile.user).exists()

    membership_url = 'https://www.warwicksu.com/membershipapi/listMembers/{token}/'.format(token=api_token)
    api_call = requests.get(membership_url)

    if api_call.status_code == 200:
        xml_root = ET.fromstring(api_call.text)
        members = list(map(lambda x: x.find('UniqueID').text, xml_root))

        return profile.uni_id in members
    else:
        messages.error(request,
                       'There was an error checking your {soc} membership, please contact an exec member.'.format(
                           soc=society), extra_tags='is-danger')

        return False


class SignupChargeView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('event_id'):
            return HttpResponseBadRequest()

        event = get_object_or_404(Event, id=request.POST.get('event_id'))

        has_signed_up = EventSignup.objects.for_event(event, request.user).exists()
        if has_signed_up:
            messages.error(request, 'You\'re already signed up to that event.', extra_tags='is-danger')
            return redirect('event_home', slug=event.slug)

        print(event.signup_count, event.signup_limit)

        # Check if there is still space left
        if event.signup_count == event.signup_limit:
            messages.error(request, 'There\'s no more space for that event, sorry.', extra_tags='is-danger')
            return redirect('event_home', slug=event.slug)

        profile = WarwickGGUser.objects.get(user=request.user)

        # If the event is hosted by UWCS
        if 'UWCS' in event.hosted_by:
            uwcs_member = check_membership(settings.UWCS_API_KEY, profile, request, 'UWCS')
        else:
            uwcs_member = False

        # If the event is hosted by Esports
        if 'WE' in event.hosted_by:
            esports_member = check_membership(settings.ESPORTS_API_KEY, profile, request, 'Esports')
        else:
            esports_member = False

        signup_cost = event.cost_member if esports_member or uwcs_member else event.cost_non_member

        # If the user should be charged but there's no stripe token then error
        if signup_cost > 0 and not request.POST.get('stripe_token'):
            return HttpResponseBadRequest()

        # If there was an issue processing the signup form then error - there shouldn't be any reason since
        # all of the fields are optional but ???
        signup = EventSignup(user=request.user, event=event)
        signup_form = SignupForm(request.POST, instance=signup)
        if not signup_form.is_valid():
            messages.error(request,
                           'There was an error processing your signup, double check everything is in order and try again.',
                           extra_tags='is-danger')
            return redirect('event_signup', slug=event.slug)

        if signup_cost > 0:
            token = request.POST.get('stripe_token')
            try:
                charge = Charge.create(amount=int(signup_cost * 100), currency='gbp', source=token,
                                       receipt_email=request.user.email)
            except StripeError:
                # If there was an error with the request
                messages.error(request,
                               'There was an error processing the payment. Please check your balance and try again later.',
                               extra_tags='is-danger')
                return redirect('event_signup', slug=event.slug)

            if charge.paid:
                signup = signup_form.save(commit=False)
                signup.transaction_token = charge.stripe_id
                signup.save()

                messages.success(request, 'Signup successful!{seating}'.format(
                    seating=' You can now reserve a seat on the seating plan.' if event.has_seating else ''),
                                 extra_tags='is-success')
                return redirect('event_home', slug=event.slug)
            else:
                messages.error(request,
                               'There was an error processing your payment. Make sure you have sufficient balance and try again.',
                               extra_tags='is-danger')
                return redirect('event_signup', slug=event.slug)
        else:
            signup_form.save()
            messages.success(request, 'Signup successful!{seating}'.format(
                seating=' You can now reserve a seat on the seating plan.' if event.has_seating else ''),
                             extra_tags='is-success')
            return redirect(event.get_absolute_url() + '#signup')


class SignupFormView(LoginRequiredMixin, View):
    template_name = 'events/signup_view.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = EventSignup.objects.for_event(event, request.user).exists()
        if has_signed_up:
            messages.error(request, 'You\'re already signed up to that event.', extra_tags='is-danger')
            return redirect('event_home', slug=slug)

        profile = WarwickGGUser.objects.get(user=request.user)

        # If the event is hosted by UWCS
        if 'UWCS' in event.hosted_by:
            uwcs_member = check_membership(settings.UWCS_API_KEY, profile, request, 'UWCS')
        else:
            uwcs_member = False

        # If the event is hosted by Esports
        if 'WE' in event.hosted_by:
            esports_member = check_membership(settings.ESPORTS_API_KEY, profile, request, 'Esports')
        else:
            esports_member = False

        is_host_member = esports_member or uwcs_member
        signup_cost = event.cost_member if is_host_member else event.cost_non_member

        signup_form = SignupForm()

        ctx = {
            'event': event,
            'event_cost': signup_cost,
            'stripe_cost': 100 * signup_cost,
            'is_host_member': is_host_member,
            'stripe_pubkey': settings.STRIPE_PUBLIC_KEY,
            'signup_form': signup_form
        }
        return render(request, self.template_name, context=ctx)


class UnsignupFormView(LoginRequiredMixin, View):
    template_name = 'events/unsignup_view.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = EventSignup.objects.for_event(event, request.user).exists()

        if not has_signed_up:
            messages.error(request, 'You cannot un-signup from an event you\'re not signed up to.',
                           extra_tags='is-danger')
            return redirect('event_home', slug=slug)

        ctx = {
            'event': event
        }
        return render(request, self.template_name, context=ctx)


class UnsignupConfirmView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        if not request.POST.get('event_id'):
            return HttpResponseBadRequest()

        event = get_object_or_404(Event, id=request.POST.get('event_id'))
        signup = EventSignup.objects.for_event(event, request.user).first()

        if not signup:
            messages.error(request, 'You cannot un-signup from an event you\'re not signed up to.',
                           extra_tags='is-danger')
            return redirect('event_home', slug=event.slug)

        # If the
        if signup.transaction_token:
            try:
                refund = Refund.create(charge=signup.transaction_token)
                signup.refund_token = refund.stripe_id
            except StripeError:
                messages.error(request,
                               'There was an error processing your refund. Please contact a member of the exec.',
                               extra_tags='is-danger')

        signup.is_unsigned_up = True
        signup.unsigned_up_at = timezone.now()
        signup.save()
        # Remove all seating references
        Seating.objects.for_event(event).filter(user=request.user).delete()

        messages.info(request, 'Successfully un-signed up from {event}.'.format(event=event.title),
                      extra_tags='is-info')
        return redirect('event_home', slug=event.slug)
