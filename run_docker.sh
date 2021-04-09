# remove the volumes along with the containers
docker-compose down -v
# # clear cache
# docker system prune -a

docker-compose up -d --build
sleep 10s
docker-compose exec anytask python manage.py makemigrations
docker-compose exec anytask python manage.py migrate --run-syncdb

docker-compose exec db bash -c "mysql --user=root --password=\"\$MYSQL_ROOT_PASSWORD\"\
    --execute=\"
    CREATE DATABASE \$DATABASE_NAME;                                            # reviewboard db
    CREATE USER '\$DATABASE_USERNAME'@'%' IDENTIFIED BY '\$DATABASE_PASSWORD';  # reviewboard user
    GRANT ALL PRIVILEGES ON \$DATABASE_NAME.* TO '\$DATABASE_USERNAME'@'%';
    GRANT ALL PRIVILEGES ON test_\$MYSQL_DATABASE.* TO '\$MYSQL_USER'@'%';      # for manage.py test
    \""

docker-compose exec anytask python manage.py test

