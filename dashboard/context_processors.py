from django.conf import settings


def has_launched(request):
    return {'HAS_LAUNCHED': settings.HAS_LAUNCHED}
