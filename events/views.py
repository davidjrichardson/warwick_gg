import json
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
import stripe
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from stripe.error import StripeError

from events.forms import EventSignupForm, TournamentSignupForm
from events.models import Event, EventSignup, Tournament, Ticket, TournamentSignup
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

        signup = None
        ticket_status = None
        if request.user.is_authenticated:
            try:
                signup = list(
                    filter(lambda x: x.is_valid(), EventSignup.objects.for_event(event, request.user).all())).pop()
            except IndexError:
                signup = None

            try:
                ticket_status = list(
                    filter(lambda x: x.ticket,
                           EventSignup.objects.for_event(event, request.user).all())).pop().ticket_status()
            except IndexError:
                ticket_status = None

        if signup:
            signups = event.signups
        else:
            signups = []

        comment_form = EventSignupForm(instance=signup)

        ctx = {
            'event': event,
            'has_signed_up': signup,
            'ticket_status': ticket_status,
            'signups_open': event.signups_open(request.user),
            'signup_start': event.signup_start_for_user(request.user),
            'signups_remaining': event.signup_limit - event.signup_count,
            'signups': signups,
            'tournaments': Tournament.objects.for_event(event),
            'comment_form': comment_form,
            'is_exec': WarwickGGUser.objects.get(user=request.user).is_exec if request.user.is_authenticated else False
        }

        return render(request, self.template_name, context=ctx)


class UpdateCommentView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('event-slug'):
            return HttpResponseBadRequest()

        event = get_object_or_404(Event, slug=request.POST.get('event-slug'))
        try:
            signup = [x for x in EventSignup.objects.for_event(event, user=request.user) if x.is_valid()].pop()
        except IndexError:
            notification = render_to_string('events/partial/notification.html', {
                'type': 'danger',
                'message': 'You aren\'t signed up to that event.'
            })

            return HttpResponse(status=403, content=notification)

        signup_form = EventSignupForm(request.POST, instance=signup)

        if not signup_form.is_valid():
            notification = render_to_string('events/partial/notification.html', {
                'type': 'danger',
                'message': 'We couldn\'t update your comment, double check everything is in order and try again.'
            })

            return HttpResponse(status=403, content=notification)

        # Update the signup
        signup.commented_at = timezone.now()
        signup.save()

        event = signup.event
        signups = event.signups
        is_exec = 'exec' in self.request.user.groups.values_list(Lower('name'), flat=True)

        context = {
            'event': event,
            'comment_form': signup_form,
            'signups': signups,
            'has_signed_up': signup,
            'is_exec': is_exec
        }
        comments_html = render_to_string('events/partial/comments.html', context, request=request)

        return HttpResponse(status=200, content=comments_html)


class TournamentView(View):
    template_name = 'tournaments/tournament_home.html'

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        try:
            user_signup = TournamentSignup.objects.get(tournament=tournament, user=request.user, is_unsigned_up=False)
        except TournamentSignup.DoesNotExist:
            user_signup = None

        ctx = {
            'tournament': tournament,
            'user_signup': user_signup,
        }
        return render(request, self.template_name, context=ctx)


def tag_for_platform(profile: WarwickGGUser, platform: str):
    return {
        Tournament.PLATFORM_STEAM: profile.steam_user,
        Tournament.PLATFORM_BNET: profile.battle_net_user,
        Tournament.PLATFORM_LEAGUE: profile.league_user,
    }.get(platform, None)


class TournamentSignupView(LoginRequiredMixin, View):
    template_name = 'tournaments/tournament_signup.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)
        profile = WarwickGGUser.objects.get(user=request.user)

        try:
            user_signup = TournamentSignup.objects.get(tournament=tournament, user=request.user, is_unsigned_up=False)
        except TournamentSignup.DoesNotExist:
            user_signup = None

        if user_signup:
            messages.error(request, 'You\'re already signed up to that tournament.', extra_tags='is-danger')
            return redirect('tournament_home', slug=slug)

        # Check for a signup to the event (if one is needed)
        if tournament.for_event and tournament.requires_attendance:
            event_signups = list(map(lambda x: x.is_valid(),
                                     EventSignup.objects.for_event(tournament.for_event, request.user).all()))
            if not event_signups:
                messages.error(request,
                               'You need to sign up to {event} before you can sign up for this tournament.'.format(
                                   event=tournament.for_event.title), extra_tags='is-danger')
                return redirect('tournament_home', slug=slug)

        platform_placeholder = tag_for_platform(profile, tournament.platform)
        platform_form = TournamentSignupForm()

        ctx = {
            'tournament': tournament,
            'form': platform_form,
            'platform_placeholder': platform_placeholder
        }
        return render(request, self.template_name, context=ctx)


class TournamentUnsignupView(LoginRequiredMixin, View):
    template_name = 'tournaments/tournament_unsignup.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        signup_exists = TournamentSignup.objects.for_tournament(tournament=tournament, user=request.user).exists()
        if not signup_exists:
            messages.error(request, 'You are not signed up to {tournament}'.format(tournament=tournament.title),
                           extra_tags='is-danger')
            return redirect('tournament_home', slug=tournament.slug)

        ctx = {
            'tournament': tournament,
        }
        return render(request, self.template_name, context=ctx)


class TournamentSignupChargeView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('tournament_id'):
            messages.error(request, 'Error signing up, refresh the page and try again', extra_tags='is-danger')
            return redirect('tournament_index')

        tournament = get_object_or_404(Tournament, id=request.POST.get('tournament_id'))

        signup_exists = TournamentSignup.objects.for_tournament(tournament, request.user).exists()
        if signup_exists:
            messages.error(request, 'You\'re already signed up to {tournament}'.format(tournament=tournament.title),
                           extra_tags='is-danger')
            return redirect('tournament_home', slug=tournament.slug)

        if tournament.signups_remaining <= 0:
            messages.error(request, 'Cannot sign up because there are no more spaces in this tournament',
                           extra_tags='is-danger')
            return redirect('tournament_home', slug=tournament.slug)

        signup = TournamentSignup(user=request.user, tournament=tournament)
        signup_form = TournamentSignupForm(request.POST, instance=signup)
        if not signup_form.is_valid():
            messages.error(request, 'Failed to create a sign up for the tournament, refresh the page and try again',
                           extra_tags='is-danger')
            return redirect('tournament_home', slug=tournament.slug)

        # Everything is good so we save the signup and redirect
        signup_form.save()
        messages.success(request, 'Success! You\'re signed up to {tournament}'.format(tournament=tournament.title),
                         extra_tags='is-success')

        return redirect('tournament_home', slug=tournament.slug)


class TournamentUnsignupConfirmView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('tournament_id'):
            messages.error(request, 'Error un-signing up, refresh the page and try again', extra_tags='is-danger')
            return redirect('tournament_index')

        tournament = get_object_or_404(Tournament, id=request.POST.get('tournament_id'))
        try:
            signup = TournamentSignup.objects.for_tournament(tournament=tournament, user=request.user).get()
        except TournamentSignup.DoesNotExist:
            messages.error(request, 'You aren\'t signed up to {tournament}'.format(tournament=tournament.title))
            return redirect('tournament_home', slug=tournament.slug)

        signup.is_unsigned_up = True
        signup.save()
        messages.success(request, 'Successfully un-signed up from {tournament}'.format(tournament=tournament.title),
                         extra_tags='is-success')

        return redirect('tournament_home', slug=tournament.slug)


class TournamentIndexView(LoginRequiredMixin, View):
    template_name = 'tournaments/tournament_index.html'
    login_url = '/accounts/login/'

    def get(self, request):
        tournaments = Tournament.objects.filter(start__gte=timezone.now()).order_by('start').all()

        ctx = {
            'tournaments': tournaments
        }
        return render(request, self.template_name, context=ctx)


class DeleteCommentView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request):
        if not request.POST.get('comment-id'):
            return HttpResponseBadRequest()

        signup = get_object_or_404(EventSignup, id=request.POST.get('comment-id'))

        if signup.user == request.user \
                or 'exec' in self.request.user.groups.values_list(Lower('name'), flat=True):
            signup.comment = ''
            signup.save()

            event = signup.event
            comment_form = EventSignupForm(instance=signup)
            signups = event.signups
            is_exec = 'exec' in self.request.user.groups.values_list(Lower('name'), flat=True)

            try:
                user_signup = [x for x in EventSignup.objects.for_event(signup.event, user=request.user) if
                               x.is_valid()].pop()
            except IndexError:
                user_signup = None

            context = {
                'event': event,
                'comment_form': comment_form,
                'signups': signups,
                'has_signed_up': user_signup,
                'is_exec': is_exec
            }
            comments_html = render_to_string('events/partial/comments.html', context, request=request)

            return HttpResponse(status=200, content=comments_html)
        else:
            notification = render_to_string('events/partial/notification.html', {
                'type': 'danger',
                'message': 'You don\'t have exec privileges to delete that comment'
            })

            return HttpResponse(status=403, content=notification)


def check_membership(api_token, profile, request, society):
    if society == 'UWCS':
        return SocialAccount.objects.filter(user=profile.user).exists()

    membership_url = 'https://www.warwicksu.com/membershipapi/listMembers/{token}/'.format(token=api_token)
    api_call = requests.get(membership_url)

    if api_call.status_code == 200:
        xml_root = ET.fromstring(api_call.text)
        members = list(map(lambda x: x.find('UniqueID').text, xml_root))

        return profile.uni_id.lower().strip('u') in members
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

        has_signed_up = list(
            filter(lambda x: x.is_complete(), EventSignup.objects.for_event(event, request.user).all()))
        if has_signed_up:
            messages.error(request, 'You\'re already signed up to that event.', extra_tags='is-danger')
            return redirect('event_home', slug=event.slug)

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

        # If there was an issue processing the signup form then error - there shouldn't be any reason since
        # all of the fields are optional but ???
        signup = EventSignup(user=request.user, event=event)
        signup_form = EventSignupForm(request.POST, instance=signup)
        if not signup_form.is_valid():
            messages.error(request,
                           'There was an error processing your signup, double check everything is in order and try again.',
                           extra_tags='is-danger')
            return redirect('event_signup', slug=event.slug)

        if signup_cost > 0:
            # This shouldn't happen since the Stripe checkout should have taken over
            return HttpResponseBadRequest()
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

        has_signed_up = list(
            filter(lambda x: x.is_valid(), EventSignup.objects.for_event(event, request.user).all()))
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

        if signup_cost > 0:
            new_ticket = Ticket(user=profile.user)
            new_ticket.save()

            ticket_json = json.dumps({
                'ticket': new_ticket.id,
                'event': event.id,
                'created_at': timezone.now().strftime('%Y-%m-%dT%H:%M:%S%z')
            })

            checkout_session = stripe.checkout.session.Session.create(
                success_url='https://{base}/events/{slug}#signup'.format(base=settings.CHECKOUT_BASE_URL,
                                                                         slug=event.slug),
                cancel_url='https://{base}/events/{slug}#signup'.format(base=settings.CHECKOUT_BASE_URL,
                                                                        slug=event.slug),
                client_reference_id=ticket_json,
                customer_email=request.user.email,
                payment_method_types=['card'],
                line_items=[{
                    'name': '{title} ticket'.format(title=event.title),
                    'currency': 'gbp',
                    'amount': int(signup_cost * 100),
                    'quantity': 1,
                    'description': 'A ticket to {title}, an event run by the Uni of Warwick Computing Society.'.format(
                        title=event.title)
                }]
            )
        else:
            checkout_session = None

        ctx = {
            'event': event,
            'event_cost': signup_cost,
            'is_host_member': is_host_member,
            'stripe_pubkey': settings.STRIPE_PUBLIC_KEY,
            'checkout_session': checkout_session.id if checkout_session else ''
        }
        return render(request, self.template_name, context=ctx)


class UnsignupFormView(LoginRequiredMixin, View):
    template_name = 'events/unsignup_view.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        has_signed_up = list(
            filter(lambda x: x.is_valid(), EventSignup.objects.for_event(event, request.user).all()))

        if not has_signed_up:
            messages.error(request, 'You cannot un-signup from an event you\'re not signed up to.',
                           extra_tags='is-danger')
            return redirect('event_home', slug=slug)

        ctx = {
            'event': event
        }
        return render(request, self.template_name, context=ctx)


class StripeWebhookView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(StripeWebhookView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            # Verify the Stripe signature
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_KEY)
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            ticket_info = json.loads(session['client_reference_id'])
            ticket_created_at = datetime.strptime(ticket_info['created_at'], '%Y-%m-%dT%H:%M:%S%z')

            # If the ticket was created after the current time, then something screwy is going on
            if ticket_created_at > timezone.now():
                return HttpResponse(status=400)

            event = Event.objects.get(id__exact=ticket_info['event'])
            ticket = Ticket.objects.get(id__exact=ticket_info['ticket'])
            user = ticket.user

            # Create the event signup for the user
            signup = EventSignup(user=user, event=event, ticket=ticket)

            # Check the charge
            payment = stripe.PaymentIntent.retrieve(session['payment_intent'])
            charge = payment['charges']['data'][0]

            # Update the ticket
            ticket.status = Ticket.IN_PROGRESS
            ticket.last_updated_at = timezone.now()
            ticket.charge_id = charge['id']

            if charge['paid']:
                ticket.status = Ticket.COMPLETE

            ticket.save()
            signup.save()
        elif event['type'] == 'charge.succeeded':
            charge = event['data']['object']

            try:
                ticket = Ticket.objects.get(charge_id__exact=charge['id'])
            except Ticket.DoesNotExist:
                # The ticket doesn't exist for some reason, refund the charge and 400
                return HttpResponse(400)

            if charge['paid']:
                ticket.status = Ticket.COMPLETE
                ticket.last_updated_at = timezone.now()
                ticket.save()
        elif event['type'] == 'charge.refunded':
            charge = event['data']['object']

            try:
                ticket = Ticket.objects.get(charge_id__exact=charge['id'])
                ticket.status = Ticket.REFUNDED
                ticket.last_updated_at = timezone.now()
                ticket.comment = 'Refunded at {time}'.format(time=timezone.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
                ticket.save()
            except Ticket.DoesNotExist:
                # Nothing needs to be done since the ticket doesn't exist and the refund has been processed
                pass

        return HttpResponse(status=200)


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

        # If the signup has a ticket then it needs to be refunded
        if signup.ticket:
            try:
                # Nothing else needs to be done since the webhook will deal with the rest of this
                stripe.Refund.create(charge=signup.ticket.charge_id)
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
