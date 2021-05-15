#!/bin/bash

sudo mkdir /var/lib/anytask /var/www/reviewboard
# build and run
docker-compose up -d --build
sudo chmod 0777 -R /var/lib/anytask /var/www/reviewboard
# init db
docker-compose exec -T db ./usr/src/init.sh
# init anytask
docker-compose exec -T anytask sh -c "
    cd anytask\
    && python manage.py makemigrations --settings=anytask.settings_production\
    && python manage.py migrate --noinput --settings=anytask.settings_production\
    && python manage.py collectstatic --no-input --clear --settings=anytask.settings_production\
    && crond"
# to provide script with proxy_params and stuff like this
sudo cp configs/nginx/nginx_anytask.conf /etc/nginx/
# start nginx
sudo nginx -c /etc/nginx/nginx_anytask.conf

