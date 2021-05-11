# This file must not be run directly.
# Execute `. deploy_local_beta/run.sh` from repository root instead.


if ! test $ANYBETA_ROOT
then
  echo "ERROR: This file should not be run directly."
  echo "Execute \`. deploy_local_beta/run.sh\` from repository root instead."
  exit 1
fi


# GIT SUBMODULES
################

ANYBETA_report
ANYBETA_report "Init submodules"
git submodule init
ANYBETA_crash_on_error
git submodule update
ANYBETA_crash_on_error

# CHOOSE RIGHT VERSION
######################

ANYBETA_PYTHON_VERSION_CHECK="from __future__ import print_function; import sys; print(int(sys.version_info < (3, 3)))"

if test `$ANYBETA_PYTHON_PATH -c "$ANYBETA_PYTHON_VERSION_CHECK"` -eq 1
then 
  . $ANYBETA_DEPLOY/deploy_local_beta_python2.sh
else
  . $ANYBETA_DEPLOY/deploy_local_beta_python3.sh
fi

# MINIO
################

if [ x"$ANYBETA_WITH_MINIO" = "x1" ]
then
  ANYBETA_report
  ANYBETA_report "Pull MinIO docker image"
  docker pull "$ANYBETA_MINIO_IMAGE"
  ANYBETA_crash_on_error
  ANYBETA_report "Start MinIO container"
  docker run --rm --detach -p 9000:9000 "$ANYBETA_MINIO_IMAGE" server /data
  sleep 5
  ANYBETA_crash_on_error
  ANYBETA_report "Create test bucket"
  s3cmd --no-ssl $ANYBETA_MINIO_OPTIONS mb s3://"$ANYBETA_MINIO_BUCKET"
  ANYBETA_crash_on_error
fi

# FINISHED
#################

ANYBETA_report
ANYBETA_report "Deploy completed!"
ANYBETA_report "You can now start django server using \`manage.py runserver\`"
