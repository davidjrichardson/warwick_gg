from django import template

register = template.Library()


@register.simple_tag()
def user_signup_date(user, event):
    if not user.is_authenticated:
        return False
    else:
        return event.signup_start_for_user(user)


@register.simple_tag()
def signups_are_open(user, event):
    if not user.is_authenticated:
        return False
    else:
        return event.signups_open(user)