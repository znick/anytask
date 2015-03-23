#!/bin/bash

[[ -f sqlite3.db ]] && echo "sqlite3.db already exists!" && exit 1

./manage.py syncdb --noinput
./manage.py migrate
./manage.py createsuperuser --username=user --email=user@example.com --noinput
echo 'from django.contrib.auth.models import User ; user=User.objects.get(username="user") ; user.set_password("qwer") ; user.save() ; print "Password changed"' | ./manage.py shell --plain
./import_test_data.sh
