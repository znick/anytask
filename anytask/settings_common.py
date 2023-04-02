# Django settings for anytask project.
# coding: utf-8

import os
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                # insert your TEMPLATE_LOADERS here
            ]
        },
    },
]

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'
LANGUAGES = (('ru', u'Русский'),)
#             ('en', 'English'))
LOCALE_PATHS = (os.path.join(PROJECT_PATH, 'locale'),)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
# USE_L10N = True

# DECIMAL_SEPARATOR = '.'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
UPLOAD_ROOT = os.path.join(PROJECT_PATH, 'upload')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
# ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.

)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3$uum*a)#mnl()ds5em&scsv9gz*!fwbqa&%apz&ccbdukyyku'

# List of callables that know how to import templates from various sources.

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'anytask.middleware.timezone_middleware.TimezoneMiddleware',
    'anytask.middleware.lang_middleware.LanguageCookieMiddleware',
)

ROOT_URLCONF = 'anytask.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            os.path.join(PROJECT_PATH, 'templates')
        ],
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                # 'django.template.loaders.eggs.Loader'
            ]
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'whoosh',
    'haystack',
    'common',
    'users',
    'years',
    'groups',
    'courses',
    'tasks',
    'registration',
    'bootstrap',
    'index',
    'crispy_forms',
    'invites',
    'anycontest',
    'issues',
    'anyrb',
    'django_extensions',
    'django_bootstrap_breadcrumbs',
    'filemanager',
    'schools',
    'jfu',
    'django_filters',
    'colorfield',
    'search',
    'staff',
    'mail',
    'reversion',
    'admission',
    'lessons',
    'api',
    'django_premailer',
)

AUTH_PROFILE_MODULE = "users.UserProfile"

ACCOUNT_ACTIVATION_DAYS = 7
INVITE_EXPIRED_DAYS = 180

RECAPTCHA_PUBLIC_KEY = "01MgZtfgTcrycDEs4Wdvd06g=="
RECAPTCHA_PRIVATE_KEY = "18ccfac9d336db9817a893ce45751d5a"

ANYSVN_SVN_URL_PREFIX = "/svn/"
ANYSVN_REPOS_PATH = "../svn/user_repos"
ANYSVN_REFFERENCE_REPO = "../new_repo"  # for new svns

RB_API_URL = "http://localhost:8080"
RB_API_USERNAME = "anytask"
RB_API_PASSWORD = "P@ssw0rd"
RB_API_DEFAULT_REVIEW_GROUP = 'teachers'
RB_SYMLINK_DIR = '/var/lib/anytask/repos/'
RB_SYMLINK_SERVICE_URL = None
RB_EXTENSIONS = ['.py', '.py2', '.py3', '.cpp', '.sage', '.m', '.java', '.h', '.cs', '.sh', '.c', '.txt', '.fs', '.hpp',
                 '.cc', '.rkt', '.sql']

FREEZED_RUN_ID_MINUTES = 30
CONTEST_API_URL = 'https://api.contest.yandex.net/anytask/'
CONTEST_V1_API_URL = 'https://api.contest.yandex.net/api/public/v2/'
CONTEST_TIME_ZONE = 'Europe/Moscow'
CONTEST_URL = "https://contest.yandex.ru/"
CONTEST_OAUTH = 'OAUTH'
CONTEST_OAUTH_ID = 'OAUTH_ID'
CONTEST_OAUTH_PASSWORD = 'OAUTH_PASSWORD'
CONTEST_EXTENSIONS = {'.py': 'python2_6', '.py2': 'python2_6', '.py3': 'python3', '.cpp': 'gcc0x', '.java': 'java8',
                      '.h': 'gcc0x', '.cs': 'mono_csharp', '.c': 'plain_c',
                      '.kt': 'kotlin'}  # Actually python2_6 is python 2.7
CONTEST_EXTENSIONS_COURSE = {
    30: {
        ".py": "python3"
    },
    13: {
        ".h": "make2"
    },
    61: {
        ".h": "make2"
    }
}

COURSES_WITH_CONTEST_MARKS = [11, 10, 65, 85, 93, 82, 79, 80, 104, 137, 160, 155]

PASSPORT_OAUTH_ID = 'OAUTH_ID'
PASSPORT_OAUTH_PASSWORD = 'PASSWORD'

IPYTHON_URL = "http://localhost:8888/notebooks"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MAX_FILE_SIZE = 100 * 1024 * 1024

EMAIL_DEFAULT_BCC = None

CRISPY_TEMPLATE_PACK = 'bootstrap4'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(PROJECT_PATH, 'search/whoosh'),
    },
}

TEST_RUNNER = 'runner.ExcludeAppsTestSuiteRunner'

TEST_EXCLUDE = [
    'reversion',
    'rbtools',
    'django_bootstrap'
]

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/users/%s/" % u.username,
}

PYTHONTASK_MAX_DAYS_WITHOUT_SCORES = 30
PYTHONTASK_MAX_DAYS_TO_FULL_CANCEL = 2
PYTHONTASK_MAX_USERS_PER_TASK = 8
PYTHONTASK_MAX_TASKS_WITHOUT_SCORE_PER_STUDENT = 2
PYTHONTASK_DAYS_DROP_FROM_BLACKLIST = 14
PYTHONTASK_MAX_INCOMPLETE_TASKS = 3

# Admission settings
YA_FORMS_OAUTH = 'TEST_YA_FORMS_OAUTH'
YA_FORMS_FIELDS = {
    'last_name': 'field_1',
    'first_name': 'field_2',
    'middle_name': 'field_3',
    'email': 'field_4',
    'phone': 'field_5',
    'birth_date': 'field_6',
    'city_of_residence': 'field_7',
    'filial': 'field_8',
    'university': 'field_9',
    'university_text': 'field_10',
    'university_in_process': 'field_11',
    'university_class': 'field_12',
    'university_class_text': 'field_13',
    'university_department': 'field_14',
    'university_year_end': 'field_15',
}
YA_FORMS_FIELDS_ADDITIONAL = {
    'additional_info': ['field_16', 'field_17', 'field_18', 'field_19'],
}
ADMISSION_DATE_END = "10.05.26 15:00"
FILIAL_STATUSES = {}
ENROLLEE_STATUS = 1

GEO_SUGGEST_URL = ''
GEOBASE_API = ''
USE_LOCAL_GEOBASE = False

PREMAILER_OPTIONS = {
    'remove_classes': True,
}

API_LANGUAGE_CODE = 'en'

JUPYTER_NBGRADER_API_URL = ''

AWS_ACCESS_KEY_ID = 'minioadmin'
AWS_SECRET_ACCESS_KEY = 'minioadmin'
AWS_S3_ENDPOINT_URL = 'http://localhost:9000'
AWS_STORAGE_BUCKET_NAME = 'anytask-test-s3'
AWS_DEFAULT_ACL = 'public-read'  # As when served by Django & FileSystemStorage
AWS_S3_USE_SSL = False

DEFAULT_FILE_STORAGE = 'anytask.storage.S3OverlayStorage'
