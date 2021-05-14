#!/bin/bash

# remove the volumes along with the containers
docker-compose down -v --remove-orphans
# clear cache if necessary
docker system prune -af
# stop nginx daemon if exists
sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop
# remove previously mounter volumes manually, otherwise get
# `django.db.utils.ProgrammingError: (1146, "Table 'rb_db.django_site' doesn't exist")`
# FIXME: too bad, but i haven't come up with a better solution
sudo rm -rf /var/lib/anytask /var/www/reviewboard

