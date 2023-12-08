# This file must be used with "source deploy_local_beta/settings.sh" *from bash*
# you cannot run it directly

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi


export ANYBETA_ROOT=$PWD
export ANYBETA_DEPLOY="$PWD/deploy_local_beta"

export ANYBETA_PYTHON_PATH="`which python3`"

export ANYBETA_VENV_NAME="anytask_venv"
export ANYBETA_VENV_DIR="$ANYBETA_ROOT/$ANYBETA_VENV_NAME"
export ANYBETA_VENV_ACTIVATE="$ANYBETA_VENV_DIR/bin/activate"

export ANYBETA_MINIO_BUCKET="anytask-test-s3"
export ANYBETA_MINIO_IMAGE="minio/minio:RELEASE.2021-03-17T02-33-02Z"
export ANYBETA_MINIO_OPTIONS="--access_key minioadmin --secret_key minioadmin --host localhost:9000 --host-bucket localhost:9000"

export ANYBETA_REPORT_PREFIX=">>>"
export ANYBETA_ERROR_PREFIX="ERROR:"


function ANYBETA_report() {
  echo -e "$ANYBETA_REPORT_PREFIX $1" 
}

function ANYBETA_error() {
  echo -e "$ANYBETA_ERROR_PREFIX $1" >&2
}

function ANYBETA_crash_on_error() {
  exit_code="$?"
  if ! test $exit_code = 0
  then
    exit $exit_code
  fi
  unset exit_code
}

function ANYBETA_usage() {
  echo "usage: deploy_local_beta.sh [-h] [-p=PYTHON_PATH]"
  echo ""
  echo "optional arguments:"
  echo "  -h, --help            show this help message and exit"
  echo "  -p=PYTHON_PATH, --python-path=PYTHON_PATH"
  echo "                        Path to python interpreter"
  echo ""
  echo "Should be run from repository root as \`. deploy_local_beta/run.sh\`"
  echo ""
  echo "Deploy local anytask beta: set up environment (settings.sh), init submodules, "
  echo "enable virtualenv, create test db."
  echo ""
  echo "settings.sh generates functions ANYBETA_activate and ANYBETA_cleanup."
  echo ""
  echo "ANYBETA_activate activates virtualenv if one exists."
  echo ""
  echo "ANYBETA_cleanup deactivates virtualenv, unsets environmental variables."
  echo "With flag -v|--rm-venv virtual environment will be removed."
  echo ""
  echo ""
}

function ANYBETA_activate() {
  . $ANYBETA_VENV_ACTIVATE
}

function ANYBETA_cleanup() {
  ANYBETA_SAVE_VENV=1
  ANYBETA_correct_args=1
  
  while (( "$#" )); do
    case $1 in
      -v|--rm-venv)
        ANYBETA_SAVE_VENV=0
        shift
        ;;
      *)
        echo "Error: unknown parameter $1"
        shift
        ANYBETA_correct_args=0
        ;;
    esac
  done

  if test $ANYBETA_correct_args = 1
  then
    deactivate

    if test $ANYBETA_SAVE_VENV -eq 0
    then
      rm -r $ANYBETA_VENV_DIR
      unset ANYBETA_VENV_DIR
    fi

    unset ANYBETA_ROOT
    unset ANYBETA_DEPLOY
    unset ANYBETA_WITH_MINIO
    unset ANYBETA_MINIO_BUCKET
    unset ANYBETA_MINIO_IMAGE
    unset ANYBETA_MINIO_OPTIONS
    unset ANYBETA_PYTHON_PATH
    unset ANYBETA_VENV_NAME
    unset ANYBETA_VENV_DIR
    unset ANYBETA_VENV_ACTIVATE
    unset ANYBETA_REPORT_PREFIX
    unset ANYBETA_ERROR_PREFIX
    unset ANYBETA_SAVE_VENV
    unset ANYBETA_DEPLOY_FILES_DIR
    unset ANYBETA_correct_args
    
    unset ANYBETA_report
    unset ANYBETA_error
    unset ANYBETA_crash_on_error
    unset ANYBETA_usage
    unset ANYBETA_activate
    unset ANYBETA_cleanup
  fi
}

export -f ANYBETA_report ANYBETA_error ANYBETA_crash_on_error \
  ANYBETA_usage ANYBETA_activate ANYBETA_cleanup


