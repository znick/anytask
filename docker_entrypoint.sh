#!/bin/sh
set -e

#until psql $DATABASE_URL -c '\l'; do
#    >&2 echo "Postgres is unavailable - sleeping"
#    sleep 1
#done

>&2 echo "Postgres is up - continuing"

if [ "$DJANGO_MANAGEPY_MIGRATE" = "on" ]; then
    /venv/bin/python manage.py migrate --noinput
fi

chown 1000:1000 -R /var/log/anytask

# See UWSGI_ENV in Dockerfile; stale files from before a restart would be summed into /metrics
rm -rf /tmp/prometheus_multiproc
mkdir -p /tmp/prometheus_multiproc
chown 1000:2000 /tmp/prometheus_multiproc

exec "$@"
