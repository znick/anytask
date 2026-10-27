# encoding: utf-8
import dj_database_url

from settings_common import *  # noqa: F403

# This is NOT a complete production settings file. For more, see:
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

import datetime
import os

DEBUG = True
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

ALLOWED_HOSTS = ['anytask.org', 'www.anytask.org', "docker.anytask.org", "beta.anytask.org"]
# e.g. the container's own name, so a metrics scraper can reach /metrics without going through nginx
ALLOWED_HOSTS += os.environ.get('EXTRA_ALLOWED_HOSTS', '').split()

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}  # noqa: F405
# Same backend, wrapped to export query count/latency/error metrics to /metrics
DATABASES['default']['ENGINE'] = DATABASES['default']['ENGINE'].replace('django.db.backends.',
                                                                        'django_prometheus.db.backends.')
# Without it mysqlclient connects as utf8 (3-byte) and emoji etc. break; ?charset= in DATABASE_URL still wins
if 'mysql' in DATABASES['default']['ENGINE']:
    DATABASES['default'].setdefault('OPTIONS', {}).setdefault('charset', 'utf8mb4')

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
            'class': 'logging.FileHandler',
            'filename': '/var/log/anytask/full.log',
            'formatter': 'verbose',
        }

    },
    # Root, not just 'django': app loggers like 'anytelegram' or __name__ ones were going nowhere
    'root': {
        'handlers': ['file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'level': LOG_LEVEL,
        },
        # Kept quiet even with LOG_LEVEL=DEBUG: a line per missing template variable
        # (dozens per page) and, while DEBUG is on, a line per SQL query
        'django.template': {
            'level': 'INFO',
        },
        'django.db.backends': {
            'level': 'INFO',
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

RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')

RB_API_URL = os.environ.get('RB_API_URL', 'https://anytask.org/rb')
RB_API_PASSWORD = os.environ.get('RB_API_PASSWORD')
RB_SYMLINK_SERVICE_URL = os.environ.get('RB_SYMLINK_SERVICE_URL')

CONTEST_OAUTH = os.environ.get('CONTEST_OAUTH', '')
CONTEST_OAUTH_ID = os.environ.get('CONTEST_OAUTH_ID')
CONTEST_OAUTH_PASSWORD = os.environ.get('CONTEST_OAUTH_PASSWORD')

PASSPORT_OAUTH_ID = os.environ.get('PASSPORT_OAUTH_ID')
PASSPORT_OAUTH_PASSWORD = os.environ.get('PASSPORT_OAUTH_PASSWORD')

IPYTHON_URL = os.environ.get("IPYTHON_URL", "http://anytask.org:8888/notebooks")

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'common.email_bcc.BCCEmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_USE_SSL = bool(os.environ.get('EMAIL_USE_SSL', False))
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = 'Anytask Robot <robot@anytask.org>'
EMAIL_DEFAULT_BCC = os.environ.get('EMAIL_DEFAULT_BCC')

COURSES_WITH_CONTEST_MARKS = [11, 10, 65, 85, 93, 82, 79, 80, 104, 137, 160, 155, 237, 214, 202, 294, 307, 277]

ALL_PAGES_MESSAGE = os.environ.get('ALL_PAGES_MESSAGE', '')
# ALL_PAGES_MESSAGE = """<div class="alert alert-warning">
# Технические работы! Anytask будет недоступен 4 апреля с 21 по 22 МСК.
# Приносим извинения за неудобства.
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

# Opt-in: serve S3 files via 7-day presigned URLs requested from the API
# instead of unsigned/guessed public URLs. Off by default to keep current
# behaviour; enable with AWS_S3_PRESIGNED_URLS_ENABLED=true.
AWS_S3_PRESIGNED_URLS_ENABLED = os.environ.get('AWS_S3_PRESIGNED_URLS_ENABLED', '').lower() in ('1', 'true', 'yes')
AWS_S3_PRESIGNED_URL_EXPIRE = int(os.environ.get('AWS_S3_PRESIGNED_URL_EXPIRE', 7 * 24 * 60 * 60))


def _aws_s3_rollout_datetime_env(var_name):
    """Parse an ISO-8601 datetime with an explicit UTC offset from an env
    var (e.g. '2026-05-01T00:00:00+00:00'). Returns None if unset. Plain
    stdlib parsing (no django.utils here) to avoid touching settings while
    this very settings module is still being built.
    """
    raw = os.environ.get(var_name)
    if not raw:
        return None
    value = datetime.datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise ValueError('{} must include a UTC offset, e.g. 2026-05-01T00:00:00+00:00'.format(var_name))
    return value


# issues.File S3 rollout (see common/s3_rollout.py). Days are opt-in tuning
# knobs; the two absolute cutover dates are unset by default (per-file
# relative delay applies) and, once set, force the rollout for ALL files.
AWS_S3_SERVE_DELAY_DAYS = int(os.environ.get('AWS_S3_SERVE_DELAY_DAYS', 210))
AWS_S3_DELETE_LOCAL_DELAY_DAYS = int(os.environ.get('AWS_S3_DELETE_LOCAL_DELAY_DAYS', 8))
AWS_S3_SERVE_AT = _aws_s3_rollout_datetime_env('AWS_S3_SERVE_AT')
AWS_S3_DELETE_LOCAL_AT = _aws_s3_rollout_datetime_env('AWS_S3_DELETE_LOCAL_AT')
