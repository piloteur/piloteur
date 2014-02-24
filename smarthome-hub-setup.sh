#!/bin/bash

set -e

sudo apt-get update
sudo apt-get install python-pip rsync
sudo pip install virtualenv

# cd to the script location
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

virtualenv ENV
if [ -f requirements.txt ]
then
    ENV/bin/pip install -r requirements.txt
fi

mkdir logs var

wget https://github.com/stedolan/jq/raw/gh-pages/download/linux64/jq
chmod +x jq
REMOTEHOST=$(./jq --raw-output .remotehost config.json)
ssh-keyscan -t ecdsa,rsa,dsa "$REMOTEHOST" >> ~/.ssh/known_hosts

SCRIPT=./smarthome-hub-runner.sh
(crontab -l ; echo "* * * * * (cd '`pwd`'; $SCRIPT)") | crontab -
