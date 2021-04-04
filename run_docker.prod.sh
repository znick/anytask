# remove the volumes along with the containers
docker-compose down -v
# # as previous (should try this in hopeless cases)
# docker volume rm anytask_static_volume anytask_media_volume anytask_mysql_data anytask_media
# # clear cache
# docker system prune -a

docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python anytask/manage.py makemigrations
docker-compose -f docker-compose.prod.yml exec web python anytask/manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec web python anytask/manage.py collectstatic --no-input --clear

# TODO: move to docker-compose
docker-compose -f docker-compose.prod.yml exec db bash -c "mysql --user=root --password=\"\$MYSQL_ROOT_PASSWORD\" --execute=\"GRANT ALL PRIVILEGES ON test_\$MYSQL_DATABASE.* TO '\$MYSQL_USER'@'%';\""
docker-compose -f docker-compose.prod.yml exec web python anytask/manage.py test

