#!/bin/bash

# TODO: un-hardcode this?
CONFIGDIR=~/smart-home-config/config

UUID=$(cat ~/.hub-id)
HUB_CONFIG="$CONFIGDIR/$UUID/config.$UUID.json"
if [ -f "$HUB_CONFIG" ]
then
    jq -s '.[0] + .[1]' "$CONFIGDIR/config.json" "$HUB_CONFIG"
else
    cat "$CONFIGDIR/config.json"
fi
