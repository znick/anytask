# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
  exit 1
fi


# PARSE ARGS
############

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
      exit 0
      ;;

    *)
      echo "Error: unknown parameter $ANYBETA_PARAM"
      exit 1
      ;;
  esac
done


# CHECK PYTHON PATH
###################

if ! test -e $ANYBETA_PYTHON_PATH
then 
  ANYBETA_error "Bad python path: $ANYBETA_PYTHON_PATH"
  exit 1
fi


# CLONE REPOSITORY
##################

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


