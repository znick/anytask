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


