#!/bin/bash

# This script will be run by cron every minute,
# and run smarthome-hub-sync.sh every 10 sec 6 times

# Workaround for cron max freq of 1 minute

for i in {0..5}
do
    ./smarthome-hub-sync.sh
    sleep 10
done
