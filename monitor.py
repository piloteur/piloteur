#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Smarthome monitor.

Usage:
  monitor.py check <hub-id>

Options:
  --listen ADDR  IP and port to bind to [default: 0.0.0.0:8080]
  -h --help      Show this screen.
  --version      Show version.

"""

import subprocess
import os.path
import json
import pipes
import sys
from docopt import docopt


def check(hub_id, config):
    ports = subprocess.check_output(["ssh", config['ssh_bridge'],
        "grep -R . '%s'" % pipes.quote(config['ssh_bridge_folder'])])
    ports = dict((l.split(':')[1].strip(), os.path.basename(l.split(':')[0]))
                 for l in ports.split('\n') if ':' in l.strip())

    if not hub_id in ports:
        return {'tunnel_up': False, 'payload': None}
        return 2

    ssh_cmd = ["ssh"]
    ssh_cmd += ["-o", "ProxyCommand ssh -e none -W %h " + pipes.quote(config['ssh_bridge'])]
    ssh_cmd += ["pi@localhost:%s" % ports[hub_id]]
    ssh_cmd += ["sudo -u smarthome python"]

    with open(os.path.join(DIR, 'payload.py')) as f:
        try:
            res = subprocess.check_output(ssh_cmd, stdin=f)
        except subprocess.CalledProcessError:
            ssh_cmd[3] = "admin@localhost:%s" % ports[hub_id]
            res = subprocess.check_output(ssh_cmd, stdin=f)

    return {'tunnel_up': True, 'payload': json.loads(res)}


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, 'config.json')) as f:
        config = json.load(f)

    arguments = docopt(__doc__, version='Smarthome monitor 0.1')
    if arguments['check']:
        json.dump(check(arguments['<hub-id>'], config), sys.stdout, indent=4)
