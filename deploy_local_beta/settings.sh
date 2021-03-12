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

function ANYBETA_activate() {
  . $ANYBETA_VENV_ACTIVATE
}

function ANYBETA_cleanup() {
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
  unset ANYBETA_cleanup
}

export -f ANYBETA_report ANYBETA_error ANYBETA_usage ANYBETA_activate


