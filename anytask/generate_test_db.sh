#!/bin/bash

[[ -f sqlite3.db ]] && echo "sqlite3.db already exists!" && exit 1

/usr/share/python/anytask/bin/python manage.py syncdb --noinput
/usr/share/python/anytask/bin/python manage.py migrate
/usr/share/python/anytask/bin/python manage.py createsuperuser --username=anytask --email=anytask@yandex.ru --noinput
echo 'from django.contrib.auth.models import User ; user=User.objects.get(username="anytask") ; user.set_password("P@ssw0rd") ; user.save() ; print "Password changed"' | /usr/share/python/anytask/bin/python manage.py shell --plain
