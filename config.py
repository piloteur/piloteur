#!/usr/bin/python

import os.path
import json
import copy
import sys
import re

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

with open(os.path.join(CONFIG_DIR, "config.json")) as f:
    config = json.load(f)

with open(os.path.expanduser('~/.hub-id')) as f:
    UUID = f.read().strip()
with open(os.path.expanduser('~/.hub-classes')) as f:
    classes = re.split(r'[^a-z0-9-]+', f.read().strip())

for name in classes + [UUID]:
    new_config_path = os.path.join(CONFIG_DIR, "hubs", name, "config.%s.json" % name)
    if os.path.isfile(new_config_path):
        with open(new_config_path) as f:
            new_config = json.load(f)
        config = dmerge(config, new_config)

json.dump(config, sys.stdout, indent=4)
