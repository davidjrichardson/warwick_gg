from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

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

# In-development sign in switch
HAS_LAUNCHED = True

ANYMAIL = {
    'SENDGRID_API_KEY': 'SENDGRID_API_KEY'
}

# Warwick SU API keys
UWCS_API_KEY = 'UWCS_API_KEY'
ESPORTS_API_KEY = 'ESPORTS_API_KEY'

# Stripe API keys
STRIPE_PUBLIC_KEY = 'STRIPE_PUBLIC_KEY'
STRIPE_PRIVATE_KEY = 'STRIPE_PRIVATE_KEY'

stripe.api_key = STRIPE_PRIVATE_KEY

try:
    from .local import *
except ImportError:
    pass
