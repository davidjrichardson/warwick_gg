from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import WarwickGGUser


class WarwickGGUserInline(admin.StackedInline):
    model = WarwickGGUser


class WarwickGGUserAdmin(BaseUserAdmin):
    inlines = [
        WarwickGGUserInline
    ]

    def nickname(self, obj):
        return WarwickGGUser.objects.get(user=obj).nickname

    def uni_id(self, obj):
        return WarwickGGUser.objects.get(user=obj).uni_id


WarwickGGUserAdmin.list_display = ('uni_id', 'nickname', 'email', 'first_name', 'last_name', 'is_staff')
WarwickGGUserAdmin.search_fields = ('warwickgguser__uni_id', 'warwickgguser__nickname', 'first_name', 'last_name', 'email')

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), WarwickGGUserAdmin)
