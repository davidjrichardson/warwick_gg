import json
import sys

from functools import reduce

from django.conf import settings
from django.db import models
from django.utils import timezone
from markdown_deux.templatetags.markdown_deux_tags import markdown_allowed
from multiselectfield import MultiSelectField

from uwcs_auth.models import WarwickGGUser


class SeatingRoom(models.Model):
    name = models.CharField(max_length=100)
    seating_plan_svg = models.FileField(upload_to='seating/')
    """
    This field will contain a literal array of integers in JSON list notation ([2, 3, 4, 5]). Each position
    corresponds to a table, and the value is the total seats on that table. For example: [20, 20, 20, 10] would
    be the standard LIB2 set up.
    """
    tables_raw = models.TextField(
        help_text='This field will contain a literal array of integers in JSON list notation ([2, 3, 4, 5]). Each position corresponds to a table, and the value is the total seats on that table. For example: [20, 20, 20, 10] would be the standard LIB2 set up.')

    @property
    def tables(self):
        tables = json.loads(self.tables_raw)
        return {k: v for k, v in enumerate(tables)}

    @property
    def tables_pretty(self):
        return ',\n'.join(map(lambda i: 'Table {k}: {v} seats'.format(k=(i[0] + 1), v=i[1]), self.tables.items()))

    @property
    def max_capacity(self):
        return reduce(lambda x, y: x + y, self.tables.values())

    def save_tables(self, tables):
        self.tables_raw = json.dumps(tables)

    def __str__(self):
        return self.name


class Event(models.Model):
    SOCIETY_CHOICES = (
        ('UWCS', 'Uni of Warwick Computing Society'),
        ('WE', 'Warwick Esports'),
    )

    id = models.AutoField(primary_key=True)

    # Event display information
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text=markdown_allowed())
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=100)

    # Signup information
    signup_start = models.DateTimeField(default=timezone.now)
    signup_end = models.DateTimeField(default=timezone.now)
    signup_start_fresher = models.DateTimeField(blank=True, null=True)
    signup_limit = models.IntegerField(default=70)

    # Society eligibility criteria
    hosted_by = MultiSelectField(blank=True, choices=SOCIETY_CHOICES, max_choices=2)
    cost_member = models.DecimalField(default=0, decimal_places=2, max_digits=3)
    cost_non_member = models.DecimalField(default=5, decimal_places=2, max_digits=3)

    # Routing
    slug = models.SlugField(max_length=40, unique=True)

    # Seating plan
    has_seating = models.BooleanField(default=True)
    seating_location = models.ForeignKey(SeatingRoom, on_delete=models.PROTECT, blank=True, null=True)
    seating_lock_time = models.DateTimeField(blank=True, null=True)

    # Signup options
    has_photography = models.BooleanField(default=False)
    has_livestream = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def __bytes__(self):
        return bytes(self.title.encode()) + bytes(self.id) + bytes(str(self.start).encode())

    def get_absolute_url(self):
        return '/events/{slug}'.format(slug=self.slug)

    @property
    def signups(self):
        signups = EventSignup.objects.filter(event=self, is_unsigned_up=False).exclude(comment__exact='').order_by(
            'commented_at', '-created_at').all()

        return signups

    @property
    def signups_all(self):
        signups = EventSignup.objects.filter(event=self, is_unsigned_up=False).order_by('-created_at').all()

        return signups

    @property
    def signup_count(self):
        return len(self.signups_all)

    @property
    def signups_left(self):
        return self.signup_limit - self.signup_count

    @property
    def seating_is_locked(self):
        if not self.seating_lock_time:
            return False
        else:
            return timezone.now() > self.seating_lock_time

    def signup_start_for_user(self, user):
        if self.signup_start_fresher:
            if not user.is_authenticated:
                return self.signup_start
            else:
                profile = WarwickGGUser.objects.get(user=user)

                return self.signup_start_fresher if profile.is_fresher else self.signup_start
        else:
            return self.signup_start

    def signups_open(self, user):
        return self.signup_start_for_user(user) < timezone.now() <= self.signup_end

    @property
    def is_ongoing(self):
        if self.start < timezone.now() <= self.end:
            return True
        else:
            return False


class TicketManager(models.Manager):
    def for_event(self, event: Event):
        return self.filter(eventsignup__event=event)

    def is_complete(self):
        return self.filter(status=Ticket.COMPLETE)

    def is_created(self):
        return self.filter(status=Ticket.CREATED)

    def is_refunded(self):
        return self.filter(status=Ticket.REFUNDED)


class Ticket(models.Model):
    COMPLETE = 'C'
    REFUNDED = 'R'
    IN_PROGRESS = 'P'
    CREATED = 'N'

    TICKET_STATUSES = (
        (COMPLETE, 'Complete'),
        (REFUNDED, 'Refunded'),
        (IN_PROGRESS, 'In progress'),
        (CREATED, 'Created')
    )

    id = models.AutoField(primary_key=True)
    charge_id = models.TextField(blank=True)
    status = models.CharField(
        max_length=1,
        choices=TICKET_STATUSES,
        default=CREATED
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    last_updated_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True)

    objects = TicketManager()

    def is_complete(self):
        return self.status == self.COMPLETE

    def is_valid(self):
        return self.status != self.CREATED

    def __str__(self):
        return '<Ticket id={id} user={user} status={status}>'.format(status={
            self.COMPLETE: 'COMPLETE',
            self.IN_PROGRESS: 'IN_PROGRESS',
            self.REFUNDED: 'REFUNDED',
            self.CREATED: 'CREATED',
        }[self.status], id=self.id, user=self.user)

    class Meta:
        ordering = ['created_at']


class EventSignupManager(models.Manager):
    def for_event(self, event: Event, user):
        return self.filter(event=event, user=user, is_unsigned_up=False)

    def all_for_event(self, event: Event):
        return self.filter(event=event, is_unsigned_up=False)


class EventSignup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    comment = models.TextField(blank=True, null=True, max_length=1024, default='')
    commented_at = models.DateTimeField(blank=True, null=True)

    # If a user has un-signed up, their signup will persist to preserve transaction information
    # This flag will determine if a signup has been removed.
    is_unsigned_up = models.BooleanField(default=False)
    unsigned_up_at = models.DateTimeField(blank=True, null=True)

    # Stripe transaction tokens in case of refund
    ticket = models.OneToOneField(Ticket, related_name='signup', on_delete=models.CASCADE, blank=True, null=True)

    objects = EventSignupManager()

    @property
    def long_name(self):
        return self.profile.long_name

    @property
    def profile(self):
        return WarwickGGUser.objects.get(user=self.user)

    @property
    def tooltip(self):
        return self.user.get_full_name() if self.profile.nickname else None

    def is_valid(self):
        return (not self.is_unsigned_up) and (self.ticket.is_complete() if self.ticket else True)

    def ticket_status(self):
        if self.ticket:
            return self.ticket.status
        else:
            return False

    def __str__(self):
        return '{user}\'s signup to {event}'.format(user=self.user, event=self.event)

    class Meta:
        ordering = ['created_at']


class TournamentManager(models.Manager):
    def for_event(self, event):
        return self.filter(for_event=event)


class Tournament(models.Model):
    PLATFORM_STEAM = 'S'
    PLATFORM_BNET = 'B'
    PLATFORM_LEAGUE = 'L'
    PLATFORM_SWITCH = 'N'
    PLATFORM_XBOX = 'X'
    PLATFORM_PLAYSTATION = 'P'
    PLATFORM_OTHER = 'O'

    PLATFORM_CHOICES = (
        (PLATFORM_STEAM, 'Steam'),
        (PLATFORM_BNET, 'Battle.NET'),
        (PLATFORM_LEAGUE, 'League of Legends'),
        (PLATFORM_SWITCH, 'Nintendo Switch'),
        (PLATFORM_XBOX, 'Xbox Live'),
        (PLATFORM_PLAYSTATION, 'Playstation Network'),
        (PLATFORM_OTHER, 'Other')
    )

    id = models.AutoField(primary_key=True)

    # Tournament display information
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text=markdown_allowed())
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    platform = models.CharField(max_length=1, choices=PLATFORM_CHOICES,
                                help_text='If \"other\" please specify')
    platform_other = models.CharField(max_length=64, blank=True)
    games = models.CharField(max_length=1024, blank=True,
                             help_text='A comma separated list of the game(s) played in this tournament')

    signup_start = models.DateTimeField(default=timezone.now)
    signup_end = models.DateTimeField(default=timezone.now)
    signup_limit = models.IntegerField(blank=True, null=True)

    # Associated event
    for_event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    requires_attendance = models.BooleanField(default=False)

    # Routing
    slug = models.SlugField(max_length=40, unique=True)

    objects = TournamentManager()

    def __str__(self):
        return self.title

    @property
    def signups_open(self):
        return self.signup_start < timezone.now() <= self.signup_end

    @property
    def is_onging(self):
        return self.start <= timezone.now() < self.end

    @property
    def platform_verbose(self):
        return dict(Tournament.PLATFORM_CHOICES).get(self.platform).replace('Other', self.platform_other)

    @property
    def platform_icon(self):
        return {
            Tournament.PLATFORM_STEAM: 'steam',
            Tournament.PLATFORM_BNET: 'battle-net',
            Tournament.PLATFORM_XBOX: 'xbox',
            Tournament.PLATFORM_PLAYSTATION: 'playstation',
            Tournament.PLATFORM_SWITCH: 'nintendo-switch'
        }.get(self.platform, None)

    @property
    def signup_count(self):
        return len(TournamentSignup.objects.all_for_tournament(self).all())

    @property
    def games_list(self):
        return list(map(lambda x: x.strip(), self.games.split(',')))

    @property
    def signups_remaining(self):
        return self.signup_limit - len(TournamentSignup.objects.all_for_tournament(self)) if self.signup_limit else \
            sys.maxsize

    @property
    def signups(self):
        signups = TournamentSignup.objects.filter(tournament=self, is_unsigned_up=False).exclude(comment__exact='')\
            .order_by('commented_at', '-created_at').all()

        return signups

    def user_signed_up(self, user):
        return TournamentSignup.objects.for_tournament(self, user).exists()

    def get_absolute_url(self):
        return '/events/tournament/{slug}'.format(slug=self.slug)


class TournamentSignupManager(models.Manager):
    def all_for_tournament(self, tournament):
        return self.filter(tournament=tournament, is_unsigned_up=True)

    def for_tournament(self, tournament, user):
        return self.filter(tournament=tournament, user=user, is_unsigned_up=False)


class TournamentSignup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, max_length=1024, default='')
    commented_at = models.DateTimeField(default=timezone.now)

    platform_tag = models.CharField(max_length=256)
    is_unsigned_up = models.BooleanField(default=False)

    objects = TournamentSignupManager()

    @property
    def profile(self):
        return WarwickGGUser.objects.get(user=self.user)

    @property
    def tooltip(self):
        return self.platform_tag

    @property
    def long_name(self):
        return self.profile.long_name
