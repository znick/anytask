import settings


def is_mysql_db():
    return settings.DATABASES['default'] == 'django.db.backends.mysql'
