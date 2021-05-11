docker-compose up -d --build

docker-compose exec db ./usr/src/init.sh
docker-compose exec anytask sh -c "
    cd anytask\
    && python manage.py makemigrations --settings=anytask.settings_production\
    && python manage.py migrate --noinput --settings=anytask.settings_production\
    && python manage.py collectstatic --no-input --clear --settings=anytask.settings_production\
    && crond\
    && python manage.py test --settings=anytask.settings_production"

sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop
# to provide script with proxy_params and stuff like this
sudo cp nginx_anytask.conf /etc/nginx/
sudo nginx -c /etc/nginx/nginx_anytask.conf

# to stop daemon run: `sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop`

