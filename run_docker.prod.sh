# remove the volumes along with the containers
docker-compose down -v --remove-orphans
# # clear cache
#docker system prune -a

sudo rm -rf /var/lib/anytask /var/www/reviewboard
sudo mkdir /var/lib/anytask /var/www/reviewboard
# it's an odd one, should be a better way
sudo chmod 777 /var/lib/anytask /var/www/reviewboard

docker-compose -f docker-compose.prod.yml up -d #--build
# grant access to django apps
sudo chmod 777 -R /var/lib/anytask /var/www/reviewboard

# TODO: use wait-for-it instead
sleep 10s

docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py makemigrations
docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py collectstatic --no-input --clear

# TODO: move to docker-compose
docker-compose -f docker-compose.prod.yml exec db bash -c "mysql --user=root --password=\"\$MYSQL_ROOT_PASSWORD\"\
    --execute=\"
    CREATE DATABASE \$DATABASE_NAME;                                            # reviewboard db
    CREATE USER '\$DATABASE_USERNAME'@'%' IDENTIFIED BY '\$DATABASE_PASSWORD';  # reviewboard user
    GRANT ALL PRIVILEGES ON \$DATABASE_NAME.* TO '\$DATABASE_USERNAME'@'%';
    GRANT ALL PRIVILEGES ON test_\$MYSQL_DATABASE.* TO '\$MYSQL_USER'@'%';      # for manage.py test
    \""

docker-compose -f docker-compose.prod.yml exec anytask python anytask/manage.py test

# to provide proxy_params and etc.
sudo cp nginx_anytask.conf /etc/nginx/
sudo nginx -c /etc/nginx/nginx_anytask.conf

# stop daemon
#sudo nginx -c /etc/nginx/nginx_anytask.conf -s stop

