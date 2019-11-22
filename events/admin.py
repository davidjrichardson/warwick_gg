import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from time import strftime

# Register your models here.
from events.models import Event, SeatingRoom, EventSignup, Tournament, Ticket, TournamentSignup


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    fields = (
        'title', 'games', 'platform', 'platform_other', 'start', 'end', 'description', 'for_event',
        'requires_attendance', 'signup_start', 'signup_end', 'signup_limit', 'slug'
    )
    date_hierarchy = 'start'
    list_display = ('title', 'start', 'end', 'for_event')
    list_filter = ['requires_attendance']


@admin.register(SeatingRoom)
class SeatingRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'seating_plan_svg')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    list_display = ('title', 'location', 'start', 'end', 'hosted_by', 'is_ongoing')
    list_filter = (
        'hosted_by', 'cost_member', 'cost_non_member', 'has_photography', 'has_livestream', 'seating_location')
    search_fields = ('title', 'location')
    actions = ['export_signups']

    def export_signups(self, request, queryset):
        columns = ['event_title', 'start', 'end', 'nick']
        entries = []

        for event in queryset:
            signups = EventSignup.objects.filter(event=event, is_unsigned_up=False).all()
            entries = entries + list(map(lambda x: (
                event.title, event.start.strftime('%d/%m/%y %H:%M'), event.end.strftime('%d/%m/%y %H:%M'),
                x.profile.long_name
            ), signups))

        filename = '{time}-{events}-signups.csv'.format(time=timezone.now().strftime('%d-%m-%yT%H:%M'),
                                                        events=(slugify('-'.join(map(lambda x: x.title, queryset)))))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(columns)
        writer.writerows(entries)
        return response

    export_signups.short_description = 'Export signups for info slips'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('user', 'created_at', 'status', 'comment', 'last_updated_at', 'charge_id')
    list_filter = ('user', 'status')
    search_fields = ('user__first_name', 'user__last_name')


@admin.register(EventSignup)
class EventSignupAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('event', 'long_name', 'created_at')
    list_filter = ('is_unsigned_up',)
    search_fields = ['comment', 'event__title', 'user__first_name', 'user__last_name']


@admin.register(TournamentSignup)
class TournamentSignupAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('tournament', 'long_name', 'created_at')
    list_filter = ('is_unsigned_up',)
    search_fields = ['comment', 'tournament__title', 'user__first_name', 'user__last_name']
