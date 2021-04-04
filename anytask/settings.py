# Django settings for anytask project.

from settings_common import *  # NOQA
from settings_common import TEMPLATES
import os


DEBUG = True
if os.environ.get("DEBUG") is not None:
    DEBUG = int(os.environ.get("DEBUG"))

for backend in TEMPLATES:
    backend['OPTIONS']['debug'] = DEBUG

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
if os.environ.get("DJANGO_ALLOWED_HOSTS") is not None:
    ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE"),
        "NAME": os.environ.get("SQL_DATABASE"),
        "USER": os.environ.get("SQL_USER"),
        "PASSWORD": os.environ.get("SQL_PASSWORD"),
        "HOST": os.environ.get("SQL_HOST"),
        "PORT": os.environ.get("SQL_PORT"),
        "OPTIONS": {"charset": "utf8mb4"},  # fix Incorrect string value error
    }
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_true']
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# local overrides (optional)

_settings_local = os.path.join(os.path.dirname(__file__), 'settings_local.py')
if os.path.exists(_settings_local):
    execfile(_settings_local)  # NOQA
