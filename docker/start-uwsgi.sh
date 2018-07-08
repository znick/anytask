#!/bin/sh
/app/anytask/manage.py syncdb --migrate --noinput
/usr/local/bin/uwsgi --ini /app/docker/uwsgi.ini
