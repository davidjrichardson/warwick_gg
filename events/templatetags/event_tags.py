from django import template

register = template.Library()


@register.simple_tag()
def signups_open(user, event):
    if not user.is_authenticated:
        return False
    else:
        return event.signups_open(user)