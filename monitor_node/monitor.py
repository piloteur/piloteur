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
import fnmatch
from docopt import docopt
from flask import Flask, Response, render_template, abort

import nexus
import nexus.private

YELLOW_LIMIT = datetime.timedelta(minutes=15)
RED_LIMIT = datetime.timedelta(minutes=30)

NodeData = collections.namedtuple('NodeData',
    ['hub_id', 'classes', 'config', 'timestamp', 'last_writes', 'versions', 'wifi_quality'])
NodeResult = collections.namedtuple('NodeResult',
    ['hub_id_found', 'drivers', 'timestamp', 'hub_id', 'hub_health', 'versions', 'classes', 'wifi_quality'])


class Monitor():
    def __init__(self, config):
        self.config = config

    def fetch_data(self, hub_id):
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

        iwconfig_log = nexus.private.fetch_system_logs("iwconfig")
        if not iwconfig_log: return  # TODO
        wifi_quality = iwconfig_log.split(',')[1]
        if wifi_quality == 'N/A': wifi_quality = None
        else: wifi_quality = int(wifi_quality)

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
                        last_writes=last_writes,
                        wifi_quality=wifi_quality)

    def serve_status(self, hub_id_pattern):
        if not re.match(r'^[a-z0-9-\?\*]+$', hub_id_pattern): abort(403)

        # TODO: make this persistent
        nexus.init(self.config)

        results = []
        hubs = sorted(fnmatch.filter(nexus.list_hub_ids(), hub_id_pattern))

        for hub_id in hubs:
            data = self.fetch_data(hub_id)

            if data:
                drivers = []
                versions = []

                hub_health = nexus.GREEN

                for driver_name, last_write in sorted(data.last_writes.items()):
                    health = nexus.GREEN
                    if (data.timestamp - last_write) > YELLOW_LIMIT:
                        health = nexus.YELLOW
                    if (data.timestamp - last_write) > RED_LIMIT:
                        health = nexus.RED
                    hub_health = max(hub_health, health)
                    drivers.append((driver_name,
                                    last_write.humanize(data.timestamp),
                                    last_write.format('YYYY-MM-DD HH:mm:ss ZZ'),
                                    health))

                health = nexus.GREEN
                ansible = data.versions['ansible']
                if ansible != 'ansible 1.5.3':  # TODO unhardcode?
                    health = nexus.RED
                hub_health = max(hub_health, health)
                versions.append(('ansible', ansible, 'ansible 1.5.3', health))

                del data.versions['timestamp']
                del data.versions['ansible']

                for repo, commit in data.versions.items():
                    # TODO get repo last commit and check how old is this
                    versions.append((repo, commit[:7], '', nexus.GREEN))

                if data.wifi_quality and data.wifi_quality < 30:
                    max(hub_health, nexus.YELLOW)

                results.append(NodeResult(
                    hub_id_found=(data is not None),
                    drivers=drivers,
                    timestamp=data.timestamp.format('YYYY-MM-DD HH:mm:ss ZZ'),
                    hub_id=hub_id,
                    hub_health=hub_health,
                    versions=versions,
                    classes=data.classes,
                    wifi_quality=data.wifi_quality,
                ))

        return render_template('status.html', results=results, nexus=nexus)

    def serve_index(self):
        # TODO: make this persistent
        nexus.init(self.config)
        # TODO: use the list of hubs registered to the tunneler instead
        return render_template('index.html', hubs=sorted(nexus.list_hub_ids()))

    def show_data(self, hub_id, driver_name):
        # TODO: make this persistent
        nexus.init(self.config)
        data = nexus.fetch_data(driver_name, hub_id=hub_id)
        if not data: abort(404)
        return Response(data, mimetype='text/plain')

    def show_logs(self, hub_id, driver_name):
        # TODO: make this persistent
        nexus.init(self.config)
        logs = nexus.fetch_logs(driver_name, hub_id=hub_id)
        if not logs: abort(404)
        return Response(logs, mimetype='text/plain')


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, 'config.json')) as f:
        config = json.load(f)

    M = Monitor(config)

    arguments = docopt(__doc__, version='Smarthome monitor 0.2')

    app = Flask(__name__)
    app.add_url_rule("/status/<hub_id_pattern>", 'serve_status', M.serve_status)
    app.add_url_rule("/", 'serve_index', M.serve_index)
    app.add_url_rule("/show/<hub_id>/data/<driver_name>", 'show_data', M.show_data)
    app.add_url_rule("/show/<hub_id>/logs/<driver_name>", 'show_logs', M.show_logs)
    host, port = arguments['--listen'].split(':')
    # app.debug = True
    app.run(host, int(port))
