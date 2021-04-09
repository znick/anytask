# remove the volumes along with the containers
docker-compose down -v
# # clear cache
#docker system prune -a

docker-compose -f docker-compose.prod.yml up -d --build

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

