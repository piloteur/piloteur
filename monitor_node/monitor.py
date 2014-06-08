#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Smarthome monitor.

Usage: monitor.py serve [--listen=<addr>]

Options:
  --listen ADDR  IP and port to bind to [default: 0.0.0.0:8080]
  -h --help      Show this screen.
  --version      Show version.

"""

import subprocess
import os.path
import json
import re
import arrow
import datetime
import collections
from docopt import docopt
from flask import Flask, render_template, abort

import nexus
import nexus.private

HEALTHY_LIMIT = datetime.timedelta(minutes=5)

NodeData = collections.namedtuple('NodeData',
    ['hub_id', 'classes', 'config', 'timestamp',
     'last_writes', 'versions'])


class Monitor():
    def __init__(self, config):
        self.config = config

    def fetch_data(self, hub_id):
        # TODO: make this persistent
        nexus.init(self.config)
        nexus.private.set_hub_id(hub_id)

        classes_log = nexus.private.fetch_system_logs("classes")
        if not classes_log: return
        remote_hub_id = classes_log.split(',')[0]
        if not remote_hub_id == hub_id: return
        classes = classes_log.split(',')[1:]

        config_cmd = [os.path.expanduser("~/smarthome-hub-sync/config.py")]
        config_cmd.append(hub_id)
        config_cmd.extend(classes)
        node_config = json.loads(subprocess.check_output(config_cmd))

        timesync_log = nexus.private.fetch_system_logs("timesync")
        if not timesync_log: return  # TODO
        timestamp = arrow.get(timesync_log.split(',')[0])

        versions_log = nexus.private.fetch_system_logs("versions")
        if not versions_log: return  # TODO
        versions = versions_log.split(',')
        versions = dict(zip((
            "timestamp",
            "ansible",
            "smart-home-config",
            "smarthome-deployment-blobs",
            "smarthome-drivers",
            "smarthome-hub-sync",
            "smarthome-reverse-tunneler",
        ), versions))

        last_writes = {}
        for driver_name in node_config['loaded_drivers']:
            t = nexus.data_timestamp(driver_name)
            if not t:
                last_writes[driver_name] = arrow.get(0)
            else:
                last_writes[driver_name] = arrow.get(t)

        return NodeData(hub_id=hub_id,
                        classes=classes,
                        config=node_config,
                        timestamp=timestamp,
                        versions=versions,
                        last_writes=last_writes)

    def serve_status(self, hub_id):
        if not re.match(r'^[a-z0-9-]+$', hub_id): abort(403)

        data = self.fetch_data(hub_id)

        drivers = []
        versions = []
        timestamp = None
        classes = None
        hub_healthy = False

        if data:
            classes = data.classes

            timestamp = data.timestamp.format('YYYY-MM-DD HH:mm:ss ZZ')

            hub_healthy = True

            for driver_name, last_write in sorted(data.last_writes.items()):
                healthy = (data.timestamp - last_write) < HEALTHY_LIMIT
                if not healthy: hub_healthy = False
                drivers.append((driver_name,
                                last_write.humanize(data.timestamp),
                                last_write.format('YYYY-MM-DD HH:mm:ss ZZ'),
                                healthy))

            ansible = data.versions['ansible']
            if ansible != 'ansible 1.5.3':  # TODO unhardcode?
                hub_healthy = healthy = False
            del data.versions['timestamp']
            del data.versions['ansible']
            versions.append(('ansible', ansible, 'ansible 1.5.3', healthy))
            for repo, commit in data.versions.items():
                # TODO get repo last commit and check how old is this
                versions.append((repo, commit[:7], '', True))


        return render_template('status.html',
            hub_id_found=(data is not None),
            drivers=drivers,
            timestamp=timestamp,
            hub_id=hub_id,
            hub_healthy=hub_healthy,
            versions=versions,
            classes=classes,
        )

    def serve_index(self):
        return render_template('status_index.html')


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, 'config.json')) as f:
        config = json.load(f)

    M = Monitor(config)

    arguments = docopt(__doc__, version='Smarthome monitor 0.2')

    app = Flask(__name__)
    app.add_url_rule("/status/<hub_id>", 'serve_status', M.serve_status)
    app.add_url_rule("/status/", 'serve_index', M.serve_index)
    host, port = arguments['--listen'].split(':')
    app.debug = True
    app.run(host, int(port))
