# Django settings for anytask project.
# coding: utf-8

import os

from settings_common import *  # NOQA

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = ["localhost"]

domain = os.environ.get('DOMAIN')
if domain is not None:
    ALLOWED_HOSTS.extend(domain.split(","))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/data/db.sqlite',
    }
}
