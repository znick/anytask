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
ANYBETA_activate
ANYBETA_crash_on_error


# REQUIREMENTS
##############

ANYBETA_report
ANYBETA_report "Install requirements"
pip install 'pip>=20.3.4' 'setuptools>=44.0.0' --upgrade
ANYBETA_crash_on_error
pip install -r requirements_local.txt
ANYBETA_crash_on_error


# MANAGE DJANGO
###############

ANYBETA_report
ANYBETA_report "Manage django project"
python setup.py develop
ANYBETA_crash_on_error


# CREATE DB
###########

ANYBETA_report
ANYBETA_report "Create test database"
$ANYBETA_DEPLOY/generate_test_db.sh
ANYBETA_crash_on_error

ANYBETA_report
ANYBETA_report "Deploy completed!"
ANYBETA_report "You can now start django server using \`manage.py runserver\`"
