# Django settings for anytask project.
# coding: utf-8

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

import os
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
    ('Anna K', 'voron13e02@gmail.com'),
    ('Nickolai Zhuravlev', 'znick@znick.ru'),
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

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'
LANGUAGES = (('ru', u'Русский'),
             ('en', 'English'))
LOCALE_PATHS = (os.path.join(PROJECT_PATH, 'locale'))

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
#ADMIN_MEDIA_PREFIX = '/static/admin/'

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
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3$uum*a)#mnl()ds5em&scsv9gz*!fwbqa&%apz&ccbdukyyku'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware'
)

ROOT_URLCONF = 'anytask.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'django.core.context_processors.static',
)

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
    'south',
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
    'debug_toolbar',
    'django_bootstrap_breadcrumbs',
    'filemanager',
    'schools',
    'jfu',
    'django_filters',
    'colorfield',
    'search',
    'staff',
    'blog',
    'mail',
    'admission',
)

AUTH_PROFILE_MODULE = "users.UserProfile"

ACCOUNT_ACTIVATION_DAYS = 7
INVITE_EXPIRED_DAYS = 180

RECAPTCHA_PUBLIC_KEY = "01MgZtfgTcrycDEs4Wdvd06g=="
RECAPTCHA_PRIVATE_KEY = "18ccfac9d336db9817a893ce45751d5a"

ANYSVN_SVN_URL_PREFIX = "/svn/"
ANYSVN_REPOS_PATH = "../svn/user_repos"
ANYSVN_REFFERENCE_REPO = "../new_repo" #for new svns

RB_API_URL = "http://localhost:8080"
RB_API_USERNAME = "anytask"
RB_API_PASSWORD = "P@ssw0rd"
RB_API_DEFAULT_REVIEW_GROUP = 'teachers'
RB_SYMLINK_DIR = '/var/lib/anytask/repos/'
RB_EXTENSIONS = ['.py', '.py2', '.py3', '.cpp', '.sage', '.m', '.java', '.h', '.cs', '.sh', '.c', '.txt', '.fs', '.hpp', '.cc', '.rkt', '.sql']

CONTEST_API_URL = 'https://api.contest.yandex.net/anytask/'
CONTEST_OAUTH = 'OAUTH'
CONTEST_OAUTH_ID = 'OAUTH_ID'
CONTEST_OAUTH_PASSWORD = 'OAUTH_PASSWORD'
CONTEST_EXTENSIONS = {'.py':'python2_6', '.py2':'python2_6', '.py3':'python3', '.cpp':'gcc0x', '.java':'java8', '.h':'gcc0x', '.cs':'mono_csharp', '.c':'plain_c'} #Actually python2_6 is python 2.7
CONTEST_EXTENSIONS_COURSE = {
    30 : {
        ".py" : "python3"
    },
    13 : {
        ".h" : "make2"
    },
    61 : {
        ".h" : "make2"
    }
}

COURSES_WITH_CONTEST_MARKS = [11, 10, 65, 85, 93, 82, 79, 80, 104, 137, 160, 155]

PASSPORT_OAUTH_ID = 'OAUTH_ID'
PASSPORT_OAUTH_PASSWORD = 'PASSWORD'

IPYTHON_URL = "http://localhost:8888/notebooks"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MAX_FILE_SIZE = 100*1024*1024

EMAIL_DEFAULT_BCC = None

CRISPY_TEMPLATE_PACK = 'bootstrap4'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(PROJECT_PATH, 'search/whoosh'),
    },
}
