import os
# from anytask.settings_common import INSTALLED_APPS


DEBUG = os.environ.setdefault('DJANGO_DEBUG', 'False')
TEMPLATE_DEBUG = DEBUG

INSTALLED_APPS = list(INSTALLED_APPS) + ['jupyter']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.setdefault('DATABASE_NAME', 'postgres'),
        'USER': os.environ.setdefault('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.setdefault('DATABASE_PASS', ''),
        'HOST': os.environ.setdefault('DATABASE_HOST', ''),
        'PORT': os.environ.setdefault('DATABASE_PORT', ''),
    }
}

JUPYTER_NBGRADER_API_URL = 'http://localhost:8089'
JUPYTER_NBGRADER_AUTH_TOKEN = 'your-nbgradersk-token'
# JUPYTER_NBGRADER_DISABLED = True

JUPYTERHUB_URL = 'http://localhost'