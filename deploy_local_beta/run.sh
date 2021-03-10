#!/bin/bash

# Execute from anytask root


#TODO: check if exist:
# python 2 or 3
# pip
# virtualenv or python venv pkg
# git
# 

export ANYBETA_ROOT=$PWD
export ANYBETA_DEPLOY="$PWD/deploy_local_beta"

export ANYBETA_PYTHON_PATH="/usr/bin/python"

export ANYBETA_VENV_NAME="anytask_venv"
export ANYBETA_VENV_DIR="$ANYBETA_ROOT/$ANYBETA_VENV_NAME"
export ANYBETA_VENV_ACTIVATE="$ANYBETA_VENV_DIR/bin/activate"

export ANYBETA_REPORT_PREFIX=">>>"
export ANYBETA_ERROR_PREFIX="ERROR:"


function ANYBETA_report() {
  echo -e "$ANYBETA_REPORT_PREFIX $1" 
}

function ANYBETA_error() {
  echo -e "$ANYBETA_ERROR_PREFIX $1" 
}

function ANYBETA_usage() {
  echo "usage: deploy_local_beta.sh [-h] [-w WORKDIR] [-p PYTHON_PATH]"
  echo ""
  echo "optional arguments:"
  echo "  -h, --help            show this help message and exit"
  echo "  -w WORKDIR, --workdir WORKDIR"
  echo "                        Deploy working directory"
  echo "  -p PYTHON_PATH, --python-path PYTHON_PATH"
  echo "                        Path to python interpreter"
  echo ""
}

export -f ANYBETA_report ANYBETA_error ANYBETA_usage


# PARSE ARGS
############

ANYBETA_correct_args=1

while (( "$#" )); do
  ANYBETA_PARAM=`echo $1 | awk -F= '{ print $1 }'`
  ANYBETA_VALUE=`echo $1 | awk -F= '{ print $2 }'`

  case $ANYBETA_PARAM in
    -p|--python-path)
      ANYBETA_PYTHON_PATH=$ANYBETA_VALUE
      shift
      ;;

    -h|--help)
      ANYBETA_usage
      shift
      ;;

    *)
      ANYBETA_error "Error: unknown parameter $ANYBETA_PARAM"
      shift
      ANYBETA_correct_args=0
      ;;
  esac
done

if test $ANYBETA_correct_args = 1
then
  . $ANYBETA_DEPLOY/deploy_local_beta.sh "$@"
fi
