import json

from avatar.templatetags.avatar_tags import avatar_url
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction, DatabaseError
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.http.response import HttpResponseBase
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from events.models import Event, EventSignup
from seating.models import SeatingRevision, Seating
from uwcs_auth.models import WarwickGGUser


class SeatingFAQView(LoginRequiredMixin, View):
    template_name = 'seating/seating_faq.html'
    login_url = '/accounts/login/'

    def get(self, request):
        ctx = {}
        return render(request, self.template_name, context=ctx)


@transaction.atomic
def save_revision(seats, event, user):
    latest_revision = SeatingRevision.objects.for_event(event).first()

    if latest_revision:
        revision_number = latest_revision.number + 1
    else:
        revision_number = 0

    # Create the new objects
    new_revision = SeatingRevision(event=event, creator=user, number=revision_number)
    new_revision.save()

    for seat in seats:
        user = get_user_model().objects.get(id=seat['user_id'])
        seat_obj = Seating(user=user, seat=seat['seat_id'], revision=new_revision)
        seat_obj.save()

    return new_revision


class SeatingRoomAPISubmitRevisionView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request, event_id):
        """
        The data for this expects the following JSON format:
        {
            "seats": [
                {
                    "seat_id": <int> -- Seat number,
                    "user_id": <int> -- The user's UID
                }
            ]
        }
        The JSON should be in the POST parameter "json"

        :return: If the user is exec, a new revision to add to the revision list, otherwise nothing.
        If there was an error status code 400 is returned.
        """
        event = get_object_or_404(Event, id=event_id)

        if not EventSignup.objects.for_event(event, request.user).exists() and not WarwickGGUser.objects.get(
                user=self.request.user).is_exec:
            return HttpResponseForbidden()

        if 'json' not in request.POST:
            return HttpResponseBadRequest()

        seats_obj = json.loads(request.POST.get('json'))
        try:
            latest_revision = save_revision(seats_obj['seats'], event)
        except DatabaseError:
            return HttpResponseBadRequest()

        if WarwickGGUser.objects.get(user=self.request.user).is_exec:
            revision_dict = {
                'name': 'Revision {n}'.format(n=latest_revision.number + 1),
                'number': latest_revision.number,
                'created_at': latest_revision.created_at
            }

            return JsonResponse({
                'revision': revision_dict
            })
        else:
            return HttpResponseBase()


def seat_to_dict(seat: Seating):
    """
    Convert a seat in the DB to a dict for use in the seating front-end
    """
    profile = WarwickGGUser.objects.get(user=seat.user)

    return {
        'nickname': profile.long_name,
        'seat_id': seat.seat,
        'user_id': seat.user.id,
        'avatar': avatar_url(seat.user)
    }


def user_to_dict(user):
    """
    Convert a user to a dict for use in the seating front-end
    """
    profile = WarwickGGUser.objects.get(user=user)

    return {
        'nickname': profile.long_name,
        'avatar': avatar_url(user),
        'user_id': user.id
    }


class SeatingRoomAPIView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if not EventSignup.objects.for_event(event, request.user).exists() and not WarwickGGUser.objects.get(
                user=self.request.user).is_exec:
            return HttpResponseForbidden()

        if request.GET.get('revision'):
            # Get the revision specified or 404 if not
            revision = get_object_or_404(SeatingRevision, event=event, number=int(request.GET.get('revision')))
        else:
            revision = SeatingRevision.objects.for_event(event).first()

        # Maintain a list of users signed up to track who hasn't got a seat yet - this could probably be done with
        # joins on the DB end, but this'll work for nwo.
        unseated = set(map(lambda s: s.user, EventSignup.objects.all_for_event(event).all()))

        if revision:
            seatings = Seating.objects.for_event_revision(event=event, revision=revision.number).all()
            seated_users = set(map(lambda s: s.user, seatings))
            buckets = {}

            for seat in seatings:
                # Since we're going back in time with seats, seat already not populated will be at its latest state.
                # So we only want to modify the seat bucket if it hasn't been allocated already
                if seat.seat not in buckets:
                    buckets[seat.seat] = seat

            unseated = unseated - seated_users
            seated = list(map(seat_to_dict, buckets.values()))
        else:
            seated = []

        # Make sure the people who aren't seated also are converted to JSON properly
        unseated = list(map(user_to_dict, unseated))
        data = {
            'seated': seated,
            'unseated': unseated
        }

        return JsonResponse(data)


class SeatingRoomRevisionListAPIView(UserPassesTestMixin, LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def test_func(self):
        return WarwickGGUser.objects.get(user=self.request.user).is_exec

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if not WarwickGGUser.objects.get(user=request.user).is_exec:
            return HttpResponseForbidden()

        revisions = SeatingRevision.objects.for_event(event).all()

        # Create a list of revisions to send
        data = {
            'revisions': list(map(lambda revision: {
                'name': 'Revision {n}'.format(n=revision.number + 1),
                'number': revision.number,
                'created_at': revision.created_at
            }, revisions))
        }

        return JsonResponse(data)


class SeatingView(LoginRequiredMixin, View):
    template_name = 'seating/seating_page.html'
    login_url = '/accounts/login/'

    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)

        # Check if the user has signed up
        has_signed_up = EventSignup.objects.for_event(event, request.user).exists()

        ctx = {
            'event': event,
            'has_signed_up': has_signed_up,
            'is_exec': WarwickGGUser.objects.get(user=self.request.user).is_exec,
            'slug': slug,
        }
        return render(request, self.template_name, context=ctx)
