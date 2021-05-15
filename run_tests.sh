#!/bin/bash
# exit on error
set -ex

echo Prepare
docker-compose exec -T anytask sh -c "
    cd anytask\
    && python manage.py create_shad --settings=anytask.settings_production < ./students.xml"

#echo Test Anytask
## test django
#docker-compose exec -T anytask sh -c "
#    cd anytask\
#    && python manage.py test --settings=anytask.settings_production"
# anytask healthcheck
curl 127.0.0.1:1337
# reviewboard healthcheck
curl 127.0.0.1:1338
# TODO: cron tests

echo Test DB
# TODO: test db sync

echo Tests completed.
