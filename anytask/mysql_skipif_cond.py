import os


IS_MYSQL_DATABASE = os.environ.get("SQL_ENGINE") == 'django.db.backends.mysql'
