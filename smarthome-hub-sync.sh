#!/bin/bash

# This simple wrapper will run the python script in its virtualenv
# if no other instances are running

( flock -n 200 || exit 99

    ~/ENV/bin/python smarthome-hub-sync.py 2>&1

) 200>~/smarthome-hub-sync.lock
