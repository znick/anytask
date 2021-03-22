#!/bin/bash

if test -e $ANYBETA_ROOT/sqlite3.db
then
  rm $ANYBETA_ROOT/sqlite3.db
fi

$ANYBETA_ROOT/anytask/manage.py migrate --no-input
ANYBETA_crash_on_error

$ANYBETA_ROOT/anytask/manage.py createsuperuser --username=anytask --email=anytask@yandex.ru --noinput
ANYBETA_crash_on_error

echo 'from django.contrib.auth.models import User ; user=User.objects.get(username="anytask") ; user.set_password("pass") ; user.save() ; print "Password changed"' | $ANYBETA_ROOT/anytask/manage.py shell --plain
ANYBETA_crash_on_error

ANYBETA_report "Login: anytask"
ANYBETA_report "Password: pass"

ANYBETA_DEPLOY_FILES_DIR=$ANYBETA_ROOT/anytask/media/files/deploy_files
if ! test -d $ANYBETA_DEPLOY_FILES_DIR
then
  mkdir $ANYBETA_DEPLOY_FILES_DIR
fi
echo "print('hello')" >> $ANYBETA_DEPLOY_FILES_DIR/file1.py
echo "text" >> $ANYBETA_DEPLOY_FILES_DIR/file2.txt

$ANYBETA_ROOT/anytask/manage.py create_test_data
ANYBETA_crash_on_error
