#!/bin/bash

ANYBETA_ROOT=$PWD

ANYBETA_WORKDIR="anytask_workdir"
ANYBETA_PYTHON_PATH="/usr/bin/python"

ANYBETA_REPO="https://github.com/znick/anytask"
ANYBETA_DIR="anytask"

ANYBETA_VENV_NAME="anytask_venv"
ANYBETA_VENV_ACTIVATE="$ANYBETA_VENV_NAME/bin/activate"

ANYBETA_REPORT_PREFIX=">>>"
ANYBETA_ERROR_PREFIX="ERROR:"


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


# PARSE ARGS
############

while (( "$#" )); do
  ANYBETA_PARAM=`echo $1 | awk -F= '{ print $1 }'`
  ANYBETA_VALUE=`echo $1 | awk -F= '{ print $2 }'`

  case $ANYBETA_PARAM in
    -w|--workdir)
      ANYBETA_WORKDIR=$ANYBETA_VALUE
      shift
      ;;

    -p|--python-path)
      ANYBETA_PYTHON_PATH=$ANYBETA_VALUE
      shift
      ;;

    -h|--help)
      ANYBETA_usage
      exit 0
      ;;

    *)
      echo "Error: unknown parameter $ANYBETA_PARAM"
      exit 1
      ;;
  esac
done


# CREATE WORKDIR
################

if ! test -d $ANYBETA_WORKDIR
then
  if ! test -e $ANYBETA_WORKDIR
  then
    ANYBETA_report "Create workdir $ANYBETA_WORKDIR"
    mkdir $ANYBETA_WORKDIR
  else
    ANYBETA_error "$ANYBETA_WORKDIR already exists and is not a directory."
    exit 1
  fi
fi

cd $ANYBETA_WORKDIR


# CLONE REPOSITORY
##################

#ANYBETA_report
#ANYBETA_report "Clone repository"
#git clone $ANYTASK_REPO
#cd $ANYTASK_DIR
#git submodule init
#git submodule update
#cd ..


# CONFIGURE PYTHON
##################

ANYBETA_PYTHON_VERSION_CHECK="from __future__ import print_function; import sys; print(int(sys.version_info < (3, 3)))"

if test `$ANYBETA_PYTHON_PATH -c "$ANYBETA_PYTHON_VERSION_CHECK"` -eq 1
then 
  . $ANYBETA_ROOT/deploy_local_beta_python2.sh
else
  . $ANYBETA_ROOT/deploy_local_beta_python3.sh
fi


# CLEANUP
#########

cd $ANYBETA_ROOT

unset ANYBETA_ROOT
unset ANYBETA_WORKDIR
unset ANYBETA_PYTHON_PATH
unset ANYBETA_REPO
unset ANYBETA_DIR
unset ANYBETA_VENV_NAME
unset ANYBETA_VENV_ACTIVATE
unset ANYBETA_REPORT_PREFIX
unset ANYBETA_ERROR_PREFIX
unset ANYBETA_PARAM
unset ANYBETA_VALUE
unset ANYBETA_PYTHON_VERSION_CHECK

unset ANYBETA_report
unset ANYBETA_error
unset ANYBETA_usage
