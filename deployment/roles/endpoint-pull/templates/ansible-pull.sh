#!/bin/bash

. /etc/profile
. $HOME/.profile
cd "{{ home }}"

### STRICT MODE
set -euo pipefail
IFS=$'\n\t'

readonly CODE="{{ home }}/piloteur-code"
readonly INVENTORY="{{ home }}/inventory.ini"
readonly LOGFILE="{{ logfile }}"
readonly SYNCED_LOGFILE="{{ synced_logfile }}"
readonly REPO="{{ code_repo }}"
readonly REVISION="{{ code_rev }}"

git_init() {
    ls .git || git init .
}

git_checkout() {
    (git remote -v | grep auto-piloteur) || git remote add auto-piloteur "$REPO"
    git remote set-url auto-piloteur "$REPO"

    git fetch --all
    git reset --hard "auto-piloteur/$REVISION" || git reset --hard "$REVISION"
}

ansible_playbook() {
    cd "$CODE/deployment"

    ansible-playbook -i "$INVENTORY" endpoint_node_local.yml
}

teardown() {
    sudo mv "$LOGFILE" "$SYNCED_LOGFILE"
    sudo chown piloteur:piloteur "$SYNCED_LOGFILE"

    exit 1
}

main() {
    cd "$CODE"

    git_init >> "$LOGFILE" 2>&1 || teardown
    git_checkout >> "$LOGFILE" 2>&1 || teardown
    ansible_playbook >> "$LOGFILE" 2>&1 || teardown

    rm "$LOGFILE"
}

main
