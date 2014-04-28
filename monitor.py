#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Smarthome monitor.

Usage:
  monitor.py check <hub-id>
  monitor.py serve [--listen=<addr>]

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
import arrow
import datetime
from docopt import docopt
from flask import Flask, render_template

HEALTHY_LIMIT = datetime.timedelta(minutes=5)


class Monitor():
    def __init__(self, config):
        self.config = config

    def check(self, hub_id):
        ports = subprocess.check_output(["ssh", self.config['ssh_bridge'],
            "grep -R . '%s'" % pipes.quote(self.config['ssh_bridge_folder'])])
        ports = dict((l.split(':')[1].strip(), os.path.basename(l.split(':')[0]))
                     for l in ports.split('\n') if ':' in l.strip())

        if not hub_id in ports:
            return {'tunnel_up': False, 'payload': None}
            return 2

        ssh_cmd = ["ssh"]
        ssh_cmd += ["-o", "ProxyCommand ssh -e none -W %h " + pipes.quote(self.config['ssh_bridge'])]
        ssh_cmd += ["-o", "BatchMode yes"]
        ssh_cmd += ["-o", "StrictHostKeyChecking no"]
        ssh_cmd += ["pi@localhost:%s" % ports[hub_id]]
        ssh_cmd += ["sudo -u smarthome python"]

        with open(os.path.join(DIR, 'payload.py')) as f:
            try:
                res = subprocess.check_output(ssh_cmd, stdin=f)
            except subprocess.CalledProcessError:
                ssh_cmd[3] = "admin@localhost:%s" % ports[hub_id]
                res = subprocess.check_output(ssh_cmd, stdin=f)

        return {'tunnel_up': True, 'payload': json.loads(res)}

    def serve_status(self, hub_id):
        data = self.check(hub_id)
        drivers = []
        timestamp = None
        hub_healthy = False
        if data['payload']:
            hub_healthy = True
            now = arrow.get(data['payload']['timestamp'])
            timestamp = now.format('YYYY-MM-DD HH:mm:ss ZZ')
            for driver_name, last_write in sorted(data['payload']['last_writes'].items()):
                last_write = arrow.get(last_write)
                healthy = (now - last_write) < HEALTHY_LIMIT
                if not healthy: hub_healthy = False
                drivers.append((driver_name,
                                last_write.humanize(now),
                                last_write.format('YYYY-MM-DD HH:mm:ss ZZ'),
                                healthy))
        return render_template('status.html',
            tunnel_up=data['tunnel_up'],
            drivers=drivers,
            timestamp=timestamp,
            hub_id=hub_id,
            hub_healthy=hub_healthy)


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, 'config.json')) as f:
        config = json.load(f)

    M = Monitor(config)

    arguments = docopt(__doc__, version='Smarthome monitor 0.1')
    if arguments['check']:
        json.dump(M.check(arguments['<hub-id>']), sys.stdout, indent=4)
    if arguments['serve']:
        app = Flask(__name__)
        app.route("/status/<hub_id>")(M.serve_status)
        host, port = arguments['--listen'].split(':')
        app.run(host, int(port))
