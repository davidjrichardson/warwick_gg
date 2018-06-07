from django.contrib import admin

# Register your models here.
from events.models import Event, SeatingRoom, EventSignup, Tournament

admin.site.register(Event)
admin.site.register(Tournament)
admin.site.register(SeatingRoom)
admin.site.register(EventSignup)
