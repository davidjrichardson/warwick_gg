from django import template

register = template.Library()


@register.simple_tag()
def signups_open(user, event):
    if not user.is_authenticated:
        return False
    else:
        return event.signups_open(user)


@register.simple_tag(takes_context=True)
def user_signed_up_to_tournament(context, tournament):
    if context['request'].user.is_authenticated:
        return False
    else:
        return tournament.user_signed_up(context['request'].user)