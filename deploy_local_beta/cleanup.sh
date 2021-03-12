#!/bin/bash

ANYBETA_SAVE_VENV=1

while (( "$#" )); do
  case $1 in
    -v|--rm-venv)
      ANYBETA_SAVE_VENV=0
      shift
      ;;
    -h|--help)
      echo "With flag -v|--rm-venv virtual env will be removed."
      ;;
    *)
      echo "Error: unknown parameter $1"
      ;;
  esac
done


# CLEANUP
#########

deactivate

if test $ANYBETA_SAVE_VENV -eq 0
then
  rm -r $ANYBETA_VENV_DIR
  unset ANYBETA_VENV_DIR
fi

unset ANYBETA_ROOT
unset ANYBETA_DEPLOY
unset ANYBETA_PYTHON_PATH
unset ANYBETA_VENV_NAME
unset ANYBETA_VENV_ACTIVATE
unset ANYBETA_REPORT_PREFIX
unset ANYBETA_ERROR_PREFIX
unset ANYBETA_SAVE_VENV
unset ANYBETA_correct_args

unset ANYBETA_report
unset ANYBETA_error
unset ANYBETA_usage
unset ANYBETA_activate
