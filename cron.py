#!/usr/bin/env python2.7

import subprocess
import os, os.path
import json
import time
import re

list_filenames = lambda dirname: [x for x in os.listdir(dirname)
                    if os.path.isfile(os.path.join(dirname, x))]

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
with open(config_file) as f:
    config = json.load(f)

base_port = config['base_port']
ports_folder = os.path.expanduser(config['ports_folder'])
ports = set(p for p in list_filenames(ports_folder)
            if p.isdigit() and int(p) >= base_port)

# Give time to the cients to bind a just-assigned port
time.sleep(5)

listening_ports = set()
for line in subprocess.check_output(['netstat', '-tln']).split('\n')[2:]:
    fields = re.split(r'\s+', line)
    if len(fields) < 6: continue
    if not fields[5] == 'LISTEN': continue
    listening_ports.add(fields[3].split(':')[1])

dead_ports = ports - listening_ports
for p in dead_ports:
    os.remove(os.path.join(ports_folder, p))
