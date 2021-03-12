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

. ./deploy_local_eta/settings.sh


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
