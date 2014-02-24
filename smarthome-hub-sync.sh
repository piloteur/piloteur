#!/bin/bash

# This simple wrapper will run the python script in its virtualenv
# if no other instances are running

( flock -n 200 || exit 99

    ENV/bin/python smarthome-hub-sync.py >> ./logs/smarthome-hub-sync 2>&1

) 200>./var/smarthome-hub-sync.lock
