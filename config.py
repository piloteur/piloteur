#!/usr/bin/python

import os.path
import json
import copy
import sys

def dmerge(d1, d2):
    if not isinstance(d2, dict):
        return d2
    result = copy.deepcopy(d1)
    for k, v in d2.iteritems():
        if k in result and isinstance(result[k], dict):
            result[k] = dmerge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result

# TODO: un-hardcode this?
CONFIG_DIR = os.path.expanduser('~/smart-home-config/config')

with open(os.path.expanduser('~/.hub-id')) as f:
    UUID = f.read().strip()

with open(os.path.join(CONFIG_DIR, "config.json")) as f:
    config = json.load(f)

HUB_CONFIG = os.path.join(CONFIG_DIR, "hubs", UUID, "config.%s.json" % UUID)
if os.path.isfile(HUB_CONFIG):
    with open(HUB_CONFIG) as f:
        hub_config = json.load(f)
    config = dmerge(config, hub_config)

json.dump(config, sys.stdout, indent=4)
