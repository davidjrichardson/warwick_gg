from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS += [
    'cacd1f8f.ngrok.io',
    '*.cacd1f8f.ngrok.io',
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'l33th4x0rs'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'uwcs_warwickgg',
        'USER': 'uwcs_warwickgg',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

stripe.api_key = STRIPE_PRIVATE_KEY

# In-development sign in switch
HAS_LAUNCHED = True

try:
    from .local import *
except ImportError:
    pass
