# encoding: utf-8
import dj_database_url

from settings_common import *  # noqa: F403

# This is NOT a complete production settings file. For more, see:
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

import os

DEBUG = True

ALLOWED_HOSTS = ['anytask.org', 'www.anytask.org', "docker.anytask.org", "beta.anytask.org"]

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}  # noqa: F405

# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/anytask/full.log',
            'formatter': 'verbose',
        }

    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,

        },

    }
}

LIB_ROOT = '/var/lib/anytask/'
MEDIA_ROOT = os.path.join(LIB_ROOT, 'media')
UPLOAD_ROOT = os.path.join(LIB_ROOT, 'upload')
STATIC_ROOT = os.path.join(LIB_ROOT, 'static')
STATIC_URL = '/static/'

if not os.environ.get("ANYTASK_BETA", False):
    DEBUG = False

CONTEST_EXTENSIONS = {'.py': 'python2_6', '.py2': 'python2_6', '.py3': 'python3', '.cpp': 'gcc0x', '.java': 'java8',
                      '.h': 'gcc0x', '.cs': 'mono_csharp', '.c': 'plain_c', '.go': 'gccgo'}

RB_API_URL = os.environ.get('RB_API_URL', 'https://anytask.org/rb')
RB_API_PASSWORD = os.environ.get('RB_API_PASSWORD')
RB_SYMLINK_SERVICE_URL = os.environ.get('RB_SYMLINK_SERVICE_URL')

CONTEST_OAUTH = os.environ.get('CONTEST_OAUTH', '')
CONTEST_OAUTH_ID = os.environ.get('CONTEST_OAUTH_ID')
CONTEST_OAUTH_PASSWORD = os.environ.get('CONTEST_OAUTH_PASSWORD')

PASSPORT_OAUTH_ID = os.environ.get('PASSPORT_OAUTH_ID')
PASSPORT_OAUTH_PASSWORD = os.environ.get('PASSPORT_OAUTH_PASSWORD')

IPYTHON_URL = os.environ.get("IPYTHON_URL", "http://anytask.org:8888/notebooks")

EMAIL_BACKEND = 'common.email_bcc.BCCEmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_USE_SSL = bool(os.environ.get('EMAIL_USE_SSL', False))
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = 'Anytask Robot <robot@anytask.org>'
EMAIL_DEFAULT_BCC = os.environ.get('EMAIL_DEFAULT_BCC')

COURSES_WITH_CONTEST_MARKS = [11, 10, 65, 85, 93, 82, 79, 80, 104, 137, 160, 155, 237, 214, 202, 294, 307, 277]

ALL_PAGES_MESSAGE = ""
# ALL_PAGES_MESSAGE = """<div class="alert alert-warning">По техническим причинам некоторые прикрепленные
# файлы временно недоступны. Приносим извинения за неудобства.
# </div>"""

PYTHONTASK_MAX_DAYS_WITHOUT_SCORES = 30
PYTHONTASK_MAX_DAYS_TO_FULL_CANCEL = 2
PYTHONTASK_MAX_USERS_PER_TASK = 8
PYTHONTASK_MAX_TASKS_WITHOUT_SCORE_PER_STUDENT = 2
PYTHONTASK_DAYS_DROP_FROM_BLACKLIST = 14
PYTHONTASK_MAX_INCOMPLETE_TASKS = 3

INSTALLED_APPS = list(INSTALLED_APPS) + ['jupyter']  # noqa: F405
JUPYTER_NBGRADER_API_URL = 'https://jupyter.anytask.ru/nbg-api'
JUPYTERHUB_URL = 'https://jupyter.anytask.ru'


LANGUAGES = (('ru', u'Русский'),
             ('en', 'English'))

# FILE_UPLOAD_PERMISSIONS = 644  # 0644


AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net/'
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'anytask')
AWS_DEFAULT_ACL = 'public-read'  # As when served by Django & FileSystemStorage
AWS_S3_USE_SSL = True
AWS_QUERYSTRING_AUTH = False
