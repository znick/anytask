#!/bin/bash

set -e

MANAGE="python anytask/manage.py"

$MANAGE syncdb --noinput

$MANAGE migrate years
$MANAGE migrate groups
$MANAGE migrate courses 0022
$MANAGE migrate tasks 0036
$MANAGE migrate issues
$MANAGE migrate users 0011
$MANAGE migrate mail
$MANAGE migrate
