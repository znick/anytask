# This file must be used with "source deploy_local_beta/run.sh" *from bash*
# you cannot run it directly

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi


#TODO: check if exist:
# python 2 or 3
# pip
# virtualenv or python venv pkg
# git
# 


# SETTINGS
##########

. ./deploy_local_beta/settings.sh


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

    --with-minio)
      export ANYBETA_WITH_MINIO=1
      shift
      ;;

    *)
      ANYBETA_error "Error: unknown parameter $ANYBETA_PARAM"
      exit 1
      ;;
  esac
done


$ANYBETA_DEPLOY/deploy_local_beta.sh "$@"

ANYBETA_activate
