#!/usr/bin/env python2.7

import os, os.path
import json

hostname = raw_input()

list_filenames = lambda dirname: [x for x in os.listdir(dirname)
                    if os.path.isfile(os.path.join(dirname, x))]

config_file = os.path.expanduser('~/piloteur-config/bridge/config.json')
with open(config_file) as f:
    config = json.load(f)

base_port = config['base_port']
ports_folder = os.path.expanduser(config['ports_folder'])

while True:
    port = next(str(n) for n in range(base_port, 65535)
                if not str(n) in list_filenames(ports_folder))

    try:
        fd = os.open(os.path.join(ports_folder, port), os.O_RDWR|os.O_CREAT|os.O_EXCL, 0644)
    except OSError:
        continue
    else:
        break

os.write(fd, hostname)
os.close(fd)

print port
