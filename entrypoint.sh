#!/bin/sh

echo "Waiting for mysql..."
while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 0.1
done
echo "MySQL started"

crond

exec "$@"
