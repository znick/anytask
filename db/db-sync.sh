#!/bin/bash


/usr/bin/pt-table-sync -v --user=root --password=$MYSQL_ROOT_PASSWORD --charset utf8 --execute \
    h=127.0.0.1,D=$MYSQL_DATABASE,t=auth_user \
    h=127.0.0.1,D=$DATABASE_NAME,t=auth_user
