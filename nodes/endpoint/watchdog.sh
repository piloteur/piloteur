#!/bin/bash

# This simple wrapper will run the python script in its virtualenv
# if no other instances are running

( flock -n 200 || exit 99


    LOGS_PATH=$(jq --raw-output .logs_path < ~/config.json)
    eval LOGS_PATH="$LOGS_PATH" # Expand that ~

    # UUID=$(cat ~/.node-id)
    # LOGS_PATH="$LOGS_PATH$UUID/"

    LOG_HOUR=$(date --utc +%Y-%m-%d-%H)

    ~/ENV/bin/python -m watchdog >> ${LOGS_PATH}watchdog/watchdog.${LOG_HOUR}.log 2>&1

) 200>~/watchdog.lock
