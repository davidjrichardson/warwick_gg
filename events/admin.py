from django.contrib import admin

# Register your models here.
from events.models import Event

admin.site.register(Event)
