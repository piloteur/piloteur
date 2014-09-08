#!/bin/bash

NAME=$1
CWD="$2"

REDIRECTOR=watchdog/output-redirector.py

PYTHON=~/drivers_ENVs/$NAME/bin/python
export PYTHONPATH=~/piloteur-code/drivers/drivers

{ ./config.py | (cd "$CWD"; $PYTHON -u -m $NAME 2>&3) | ~/ENV/bin/python "$REDIRECTOR" -d $NAME; } 3>&1 1>&2 | ~/ENV/bin/python "$REDIRECTOR" -l $NAME
