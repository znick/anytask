#!/bin/sh
set -e .
cd $(dirname $0)

#git pull
git submodule init
git submodule update
docker build -f Dockerfile -t anytask ..
