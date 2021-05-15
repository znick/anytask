#!/bin/bash
# exit on error
set -ex

echo Prepare
docker-compose exec -T anytask sh -c "
    cd anytask\
    && python manage.py create_shad --settings=anytask.settings_production < ./students.xml"

echo Test Anytask
# test django
docker-compose exec -T anytask sh -c "
    cd anytask\
    && python manage.py test --settings=anytask.settings_production"
# anytask healthcheck
curl -sS 127.0.0.1:1337 > /dev/null
# reviewboard healthcheck
curl -sS 127.0.0.1:1338 > /dev/null

# TODO: cron tests
# TODO: Test DB, db sync

echo Tests completed.
