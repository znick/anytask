# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
else

  # GIT SUBMODULES
  ################

  ANYBETA_report
  ANYBETA_report "Init submodules"
  git submodule init
  git submodule update

  # CHOOSE RIGHT VERSION
  ######################

  ANYBETA_PYTHON_VERSION_CHECK="from __future__ import print_function; import sys; print(int(sys.version_info < (3, 3)))"

  if test `$ANYBETA_PYTHON_PATH -c "$ANYBETA_PYTHON_VERSION_CHECK"` -eq 1
  then 
    . $ANYBETA_DEPLOY/deploy_local_beta_python2.sh
  else
    . $ANYBETA_DEPLOY/deploy_local_beta_python3.sh
  fi

fi
