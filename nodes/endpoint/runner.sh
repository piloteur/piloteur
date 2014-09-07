#!/bin/bash

# This script will be run by cron every minute,
# and run sync.sh every 10 sec 6 times

# Workaround for cron max freq of 1 minute

for i in {0..5}
do
    ./sync.sh &
    sleep 10
done
