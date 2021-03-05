#!/bin/bash

ANYBETA_ROOT=$PWD

ANYBETA_WORKDIR="$ANYBETA_ROOT/anytask_workdir"
ANYBETA_PYTHON_PATH="/usr/bin/python"

ANYBETA_GIT_CLONE=1

ANYBETA_REMOTE="https://github.com/znick/anytask"
ANYBETA_LOCAL="$ANYBETA_WORKDIR/anytask"

ANYBETA_VENV_NAME="anytask_venv"
ANYBETA_VENV_DIR="$ANYBETA_LOCAL/$ANYBETA_VENV_NAME"
ANYBETA_VENV_ACTIVATE="$ANYBETA_VENV_DIR/bin/activate"

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

function ANYBETA_main() {

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

    --no-git-clone)
      ANYBETA_GIT_CLONE=0
      shift
      ;;

    -h|--help)
      ANYBETA_usage
      return
      ;;

    *)
      echo "Error: unknown parameter $ANYBETA_PARAM"
      return
      ;;
  esac
done


# CHECK PYTHON PATH
###################

if ! test -e $ANYBETA_PYTHON_PATH
then 
  ANYBETA_error "Bad python path: $ANYBETA_PYTHON_PATH"
  return
fi


# CREATE WORKDIR
################

if ! test -e $ANYBETA_WORKDIR
then
  ANYBETA_report "Create workdir $ANYBETA_WORKDIR"
  mkdir $ANYBETA_WORKDIR
else
  ANYBETA_error "$ANYBETA_WORKDIR already exists."
  return
fi

cd $ANYBETA_WORKDIR


# CLONE REPOSITORY
##################

if test $ANYBETA_GIT_CLONE -eq 1
then
  ANYBETA_report
  ANYBETA_report "Clone repository"
  git clone $ANYBETA_REMOTE
  cd $ANYBETA_LOCAL
  git submodule init
  git submodule update
fi


# CHOOSE RIGHT VERSION
######################

ANYBETA_PYTHON_VERSION_CHECK="from __future__ import print_function; import sys; print(int(sys.version_info < (3, 3)))"

if test `$ANYBETA_PYTHON_PATH -c "$ANYBETA_PYTHON_VERSION_CHECK"` -eq 1
then 
  . $ANYBETA_ROOT/deploy_local_beta_python2.sh
else
  . $ANYBETA_ROOT/deploy_local_beta_python3.sh
fi

} # define ANYBETA_main()


ANYBETA_main "$@"


# CLEANUP
#########

ANYBETA_report
ANYBETA_report "Cleanup"

cd $ANYBETA_ROOT

unset ANYBETA_ROOT
unset ANYBETA_WORKDIR
unset ANYBETA_PYTHON_PATH
unset ANYBETA_GIT_CLONE
unset ANYBETA_REMOTE
unset ANYBETA_LOCAL
unset ANYBETA_VENV_NAME
unset ANYBETA_VENV_DIR
unset ANYBETA_VENV_ACTIVATE
unset ANYBETA_REPORT_PREFIX
unset ANYBETA_ERROR_PREFIX
unset ANYBETA_PARAM
unset ANYBETA_VALUE
unset ANYBETA_PYTHON_VERSION_CHECK

unset ANYBETA_report
unset ANYBETA_error
unset ANYBETA_usage
unset ANYBETA_main
