from django.contrib import admin

# Register your models here.
from events.models import Event, SeatingRoom

admin.site.register(Event)
admin.site.register(SeatingRoom)
