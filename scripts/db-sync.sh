#!/bin/bash


# TODO: fix `Redundant argument in sprintf at /usr/bin/mk-table-sync line 28.` warning?
/usr/bin/mk-table-sync --charset utf8 --execute \
    'u=$MYSQL_USER,p=$MYSQL_PASSWORD,h=127.0.0.1,D=$MYSQL_DATABASE,t=auth_user'\
    'u=$DATABASE_NAME,p=$DATABASE_PASSWORD,h=127.0.0.1,D=DATABASE_NAME,t=auth_user'

