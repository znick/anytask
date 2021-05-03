# remove the volumes along with the containers
docker-compose down -v --remove-orphans
# clear cache if necessary
#docker system prune -a

sudo rm -rf /var/lib/anytask /var/www/reviewboard
sudo mkdir /var/lib/anytask /var/www/reviewboard
# TODO: more strict permissions
sudo chmod 777 /var/lib/anytask /var/www/reviewboard

docker-compose -f docker-compose.prod.yml up -d #--build

# grant access to django apps
# TODO: more strict permissions
sudo chmod 777 -R /var/lib/anytask /var/www/reviewboard

# TODO: use wait-for-it instead
sleep 10s

docker-compose -f docker-compose.prod.yml exec db ./usr/src/db-grant-access.sh
docker-compose -f docker-compose.prod.yml exec db ./usr/src/db-sync.sh

docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py makemigrations
docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py collectstatic --no-input --clear
# run cron
docker-compose -f docker-compose.prod.yml exec anytask crond
docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py test

sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop
# to provide script with proxy_params and stuff like this
sudo cp nginx_anytask.conf /etc/nginx/
sudo nginx -c /etc/nginx/nginx_anytask.conf

# to stop daemon run: `sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop`

