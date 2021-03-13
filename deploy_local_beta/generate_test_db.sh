#!/bin/bash

if test -e $ANYBETA_ROOT/sqlite3.db
then
  rm $ANYBETA_ROOT/sqlite3.db
fi
$ANYBETA_ROOT/anytask/manage.py migrate --no-input
$ANYBETA_ROOT/anytask/manage.py createsuperuser --username=anytask --email=anytask@yandex.ru --noinput
echo 'from django.contrib.auth.models import User ; user=User.objects.get(username="anytask") ; user.set_password("pass") ; user.save() ; print "Password changed"' | $ANYBETA_ROOT/anytask/manage.py shell --plain

ANYBETA_report "anytask pass"
