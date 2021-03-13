#!/bin/bash

# Execute from anytask root


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

    *)
      ANYBETA_error "Error: unknown parameter $ANYBETA_PARAM"
      exit 1
      ;;
  esac
done


$ANYBETA_DEPLOY/deploy_local_beta.sh "$@"
ANYBETA_crash_on_error

ANYBETA_activate
