# This file must be used with "source deploy_local_beta/activate.sh" *from bash*
# you cannot run it directly

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi

. deploy_local_beta/settings.sh
ANYBETA_activate
