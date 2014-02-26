#!/bin/bash

# This simple wrapper will run the python script in its virtualenv
# if no other instances are running

( flock -n 200 || exit 99

    LOGS_PATH=$(~/jq --raw-output .logs_path config.json)
    eval LOGS_PATH="$LOGS_PATH" # Expand that ~
    ~/ENV/bin/python smarthome-hub-sync.py >> ${LOGS_PATH}smarthome-hub-sync.log 2>&1

) 200>~/smarthome-hub-sync.lock
