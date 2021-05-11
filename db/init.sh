#!/bin/bash

apt-get update
apt-get install -y wget libdbd-mysql-perl libterm-readkey-perl
wget percona.com/get/pt-table-sync -P /usr/bin/
chmod +x /usr/bin/pt-table-sync


echo "Wait for mysqld to start"
while ! mysqladmin ping --silent; do
    sleep 1
done


mysql --user=root --password=$MYSQL_ROOT_PASSWORD --execute="
    CREATE DATABASE $DATABASE_NAME;
    CREATE USER '$DATABASE_USERNAME'@'%' IDENTIFIED BY '$DATABASE_PASSWORD';
    GRANT ALL PRIVILEGES ON $DATABASE_NAME.* TO '$DATABASE_USERNAME'@'%';
    GRANT ALL PRIVILEGES ON test_$MYSQL_DATABASE.* TO '$MYSQL_USER'@'%';"

