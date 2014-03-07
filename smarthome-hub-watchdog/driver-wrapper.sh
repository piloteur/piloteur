#!/bin/bash

NAME=$1

REDIRECTOR=smarthome-hub-watchdog/output-redirector.py

PYTHON=~/drivers_ENVs/$NAME/bin/python
export PYTHONPATH=~/smarthome-drivers/drivers

{ ./config.sh | $PYTHON -u -m $NAME 2>&3 | ~/ENV/bin/python "$REDIRECTOR" -d $NAME; } 3>&1 1>&2 | ~/ENV/bin/python "$REDIRECTOR" -l $NAME
