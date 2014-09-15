#!/usr/bin/python

import os.path
import json
import copy
import os

CONFIG_DIR = os.path.expanduser('~/piloteur-config/endpoint')

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

def gen_paths(config_dir):
    paths = {}
    for root, dirs, files in os.walk(config_dir):
        foldername = os.path.basename(root)
        if not "config.%s.json" % foldername in files:
            continue
        if foldername in paths:
            paths[foldername] = None
            # TODO: log an error here
        else:
            paths[foldername] = os.path.join(root, "config.%s.json" % foldername)
    return paths

def make_config(UUID, classes, config_dir=CONFIG_DIR):
    with open(os.path.join(config_dir, "config.json")) as f:
        config = json.load(f)

    config_paths = gen_paths(config_dir)
    for name in classes + [UUID]:
        if not config_paths.get(name): continue
        new_config_path = config_paths[name]
        with open(new_config_path) as f:
            new_config = json.load(f)
        config = dmerge(config, new_config)

    config["node-id"] = UUID
    config["node-classes"] = classes

    return config


# with open(os.path.expanduser('~/.node-id')) as f:
#     UUID = f.read().strip()
# with open(os.path.expanduser('~/.node-classes')) as f:
#     classes = re.split(r'[^a-z0-9-]+', f.read().strip())
