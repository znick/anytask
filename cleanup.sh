#!/bin/bash

# remove the volumes along with the containers
docker-compose down -v --remove-orphans
# clear cache if necessary
docker system prune -af
# stop nginx daemon
sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop

