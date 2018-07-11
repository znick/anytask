import os

DEBUG = os.environ.setdefault('DJANGO_DEBUG', 'False')
TEMPLATE_DEBUG = DEBUG

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