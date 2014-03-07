#!/bin/bash

NAME=$1
DRIVER=$2

REDIRECTOR=smarthome-hub-watchdog/output-redirector.py

{ ./config.sh | python -u "$DRIVER" 2>&3 | ~/ENV/bin/python "$REDIRECTOR" -d $NAME; } 3>&1 1>&2 | ~/ENV/bin/python "$REDIRECTOR" -l $NAME
