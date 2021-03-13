# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
else


#SETUP VIRTUALENV
#################

ANYBETA_report
ANYBETA_report "Enable virtualenv"

virtualenv -p $ANYBETA_PYTHON_PATH $ANYBETA_VENV_NAME
ANYBETA_activate


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


# CREATE DB
###########

ANYBETA_report
ANYBETA_report "Create test database"
$ANYBETA_DEPLOY/generate_test_db.sh
$ANYBETA_ROOT/anytask/manage.py create_test_data

ANYBETA_report
ANYBETA_report "Deploy completed!"
ANYBETA_report "You can now start django server using \`manage.py runserver\`"

fi
