# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
else


#SETUP VIRTUALENV
#################

if test -e $ANYBETA_VENV_DIR
then
  ANYBETA_report "Remove old virtualenv"
  rm -r $ANYBETA_VENV_DIR
fi

ANYBETA_report
ANYBETA_report "Enable virtualenv"

virtualenv -p $ANYBETA_PYTHON_PATH $ANYBETA_VENV_NAME
. $ANYBETA_VENV_ACTIVATE


# REQUIREMENTS
##############

ANYBETA_report
ANYBETA_report "Install requirements"
pip install 'pip>=20.3.4' 'setuptools>=44.0.0' --upgrade
pip install -r requirements_local.txt


# MANAGE DJANGO
###############

ANYBETA_report
ANYBETA_report "Manage django project"
python setup.py develop
python ./anytask/manage.py migrate --noinput
#./anytask/manage.py runserver 127.0.0.1:8019 -v 3 --traceback

fi
