# remove the volumes along with the containers
docker-compose down -v
# # as previous (should try this in hopeless cases)
# docker volume rm anytask_static_volume anytask_media_volume anytask_mysql_data anytask_media
# # clear cache
# docker system prune -a

docker-compose up -d --build

# TODO: move to docker-compose
docker-compose exec db bash -c "mysql --user=root --password=\"\$MYSQL_ROOT_PASSWORD\" --execute=\"GRANT ALL PRIVILEGES ON test_\$MYSQL_DATABASE.* TO '\$MYSQL_USER'@'%';\""
docker-compose exec web python manage.py test

