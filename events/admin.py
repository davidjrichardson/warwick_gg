from django.contrib import admin

# Register your models here.
from events.models import Event, SeatingRoom, EventSignup, Tournament


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
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


@admin.register(EventSignup)
class EventSignupAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('event', 'long_name', 'created_at', 'photography_consent')
    list_filter = ('is_unsigned_up', 'photography_consent')
    search_fields = ['comment', 'event__title', 'user__first_name', 'user__last_name']
