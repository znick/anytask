# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
  exit 1
fi


#SETUP VIRTUALENV
#################

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
$ANYBETA_PYTHON_PATH setup.py develop
./anytask/manage.py
./anytask/manage.py migrate --noinput
#./anytask/manage.py runserver 127.0.0.1:8019 -v 3 --traceback
