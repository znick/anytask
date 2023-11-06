#!/bin/bash -x

date
docker compose pull
docker compose up -d
echo Done!
date
