# Django settings for anytask project.
# coding: utf-8

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

import os

from settings_common import *  
import os

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = ["localhost"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/data/db.sqlite',
    }
}
