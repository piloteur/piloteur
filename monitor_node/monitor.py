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
import paramiko
import time
import fnmatch
from docopt import docopt
from flask import Flask, Response
from flask import render_template, abort, url_for

import nexus
import nexus.private

YELLOW_LIMIT = datetime.timedelta(minutes=15)
RED_LIMIT = datetime.timedelta(minutes=30)

def void_namedtuple(ntuple):
    void = ntuple._make([None] * len(ntuple._fields))
    def new(**kwargs):
        return void._replace(**kwargs)
    return new

NodeData = void_namedtuple(collections.namedtuple('NodeData',
    ['hub_id', 'classes', 'timestamp', 'versions', 'wifi_quality', 'error', 'last_writes', 'config']))
NodeResult = void_namedtuple(collections.namedtuple('NodeResult',
    ['hub_id', 'classes', 'timestamp', 'versions', 'wifi_quality', 'error', 'summary', 'hub_health', 'drivers']))


def get_tunnel_connections(tunnel_info):
    username, hostname, port, folder = tunnel_info

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username)

    cmd = "grep -h . {}*".format(folder)
    stdin, stdout, stderr = client.exec_command(cmd)
    return [n.strip() for n in stdout.readlines()]


class Monitor():
    def __init__(self, config):
        self.config = config
        self.last_connection = 0

    def nexus_init(self):
        # TODO: make this smarter
        if self.last_connection > time.time() - 60:
            return

        for _ in range(5):
            try:
                nexus.init(self.config)
            except paramiko.SSHException:
                continue
            self.last_connection = time.time()
            return

        abort(500)

    def fetch_data(self, hub_id):
        nexus.private.set_hub_id(hub_id)

        if hub_id not in nexus.list_hub_ids():
            return NodeData(hub_id=hub_id, error="Hub ID not found.")

        classes_log = nexus.private.fetch_system_logs("classes")
        if not classes_log:
            return NodeData(hub_id=hub_id, error="Missing classes data.")
        remote_hub_id = classes_log.split(',')[0]
        if not remote_hub_id == hub_id:
            return NodeData(hub_id=hub_id, error="Mismatching hub_id?!")
        classes = classes_log.split(',')[1:]

        config_cmd = [os.path.expanduser("~/smarthome-hub-sync/config.py")]
        config_cmd.append(hub_id)
        config_cmd.extend(classes)
        node_config = json.loads(subprocess.check_output(config_cmd))

        timesync_log = nexus.private.fetch_system_logs("timesync")
        if not timesync_log:
            return NodeData(hub_id=hub_id, error="Missing timesync data.")
        timestamp = arrow.get(timesync_log.split(',')[0])

        iwconfig_log = nexus.private.fetch_system_logs("iwconfig")
        if not iwconfig_log:
            return NodeData(hub_id=hub_id, error="Missing iwconfig data.")
        wifi_quality = iwconfig_log.split(',')[1]
        if wifi_quality == 'N/A': wifi_quality = None
        else: wifi_quality = int(wifi_quality)

        versions_log = nexus.private.fetch_system_logs("versions")
        if not versions_log:
            return NodeData(hub_id=hub_id, error="Missing versions data.")
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

    def assess_data(self, data):
        if data.error:
            return NodeResult(
                hub_id=data.hub_id,
                hub_health=nexus.RED,
                error=data.error,
            )

        drivers = []
        versions = []

        hub_health = nexus.GREEN
        error_message = ''


        ########################################################################
        # DRIVERS                                                              #
        ########################################################################
        for driver_name, last_write in sorted(data.last_writes.items()):
            health = nexus.GREEN
            if (data.timestamp - last_write) > YELLOW_LIMIT:
                health = nexus.YELLOW
            if (data.timestamp - last_write) > RED_LIMIT:
                health = nexus.RED

            if health != nexus.GREEN:
                error_message += '"{}" last logged data {}. '.format(
                    driver_name, last_write.humanize(data.timestamp))

            hub_health = max(hub_health, health)
            drivers.append((driver_name,
                            last_write.humanize(data.timestamp),
                            last_write.format('YYYY-MM-DD HH:mm:ss ZZ'),
                            health))

        ########################################################################
        # VERSIONS                                                             #
        ########################################################################
        health = nexus.GREEN
        ansible = data.versions['ansible']
        if ansible != 'ansible 1.5.3':  # TODO unhardcode?
            health = nexus.RED
            error_message += 'Old Ansible version. '
        hub_health = max(hub_health, health)
        versions.append(('ansible', ansible, 'ansible 1.5.3', health))

        del data.versions['timestamp']
        del data.versions['ansible']

        for repo, commit in data.versions.items():
            # TODO get repo last commit and check how old is this
            versions.append((repo, commit[:7], '', nexus.GREEN))

        ########################################################################
        # WI-FI QUALITY                                                        #
        ########################################################################
        if data.wifi_quality and data.wifi_quality < 30:
            hub_health = max(hub_health, nexus.YELLOW)
            error_message += 'Weak Wi-Fi signal. '


        return NodeResult(
            drivers=drivers,
            timestamp=data.timestamp.format('YYYY-MM-DD HH:mm:ss ZZ'),
            hub_id=data.hub_id,
            hub_health=hub_health,
            versions=versions,
            classes=data.classes,
            wifi_quality=data.wifi_quality,
            summary=error_message,
        )


    ### STATUS

    def serve_status(self, hub_id):
        if not re.match(r'^[a-z0-9-]+$', hub_id): abort(403)
        return render_template('status.html', hub_id=hub_id)

    def ajax_status(self, hub_id):
        if not re.match(r'^[a-z0-9-]+$', hub_id): abort(403)

        self.nexus_init()

        data = self.fetch_data(hub_id)
        result = self.assess_data(data)

        return render_template('ajax_status.html', h=result, nexus=nexus)


    ### SEARCH

    def serve_search(self, query):
        if not re.match(r'^[a-z0-9-\*\? ]+$', query): abort(403)
        return render_template('search.html', query=query)

    def ajax_search(self, query):
        if not re.match(r'^[a-z0-9-\*\? ]+$', query): abort(403)

        self.nexus_init()

        all_hubs = nexus.list_hub_ids()
        hubs = set()
        for keyword in query.split(' '):
            keyword = '*' + keyword.strip('*') + '*'
            hubs.update(fnmatch.filter(all_hubs, keyword))

        if len(hubs) == 1:
            return """
            <script>window.location.href = "{}";</script>
            """.format(url_for('serve_status', hub_id=list(hubs)[0]))

        results = []
        for hub_id in hubs:
            data = self.fetch_data(hub_id)

            res = self.assess_data(data)

            results.append((
                res.hub_id,
                res.hub_health,
                res.error or res.summary
            ))

        return render_template('ajax_search.html', results=results, nexus=nexus)


    ### INDEX

    def serve_index(self):
        return render_template('index.html')

    def ajax_index(self):
        self.nexus_init()

        hubs_list = get_tunnel_connections(self.config['tunnel_info'])
        return render_template('ajax_index.html', hubs=sorted(hubs_list))


    ### SHOW

    def show_data(self, hub_id, driver_name):
        self.nexus_init()

        data = nexus.fetch_data(driver_name, hub_id=hub_id)
        if not data: abort(404)
        return Response(data, mimetype='text/plain')

    def show_logs(self, hub_id, driver_name):
        self.nexus_init()

        logs = nexus.fetch_logs(driver_name, hub_id=hub_id)
        if not logs: abort(404)
        return Response(logs, mimetype='text/plain')


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, 'config.json')) as f:
        config = json.load(f)

    M = Monitor(config)

    arguments = docopt(__doc__, version='Smarthome monitor 0.3')

    app = Flask(__name__)

    app.add_url_rule("/", 'serve_index', M.serve_index)
    app.add_url_rule("/ajax/index/", 'ajax_index', M.ajax_index)

    app.add_url_rule("/status/<hub_id>", 'serve_status', M.serve_status)
    app.add_url_rule("/ajax/status/<hub_id>", 'ajax_status', M.ajax_status)

    app.add_url_rule("/search/<query>", 'serve_search', M.serve_search)
    app.add_url_rule("/ajax/search/<query>", 'ajax_search', M.ajax_search)

    app.add_url_rule("/show/<hub_id>/data/<driver_name>", 'show_data', M.show_data)
    app.add_url_rule("/show/<hub_id>/logs/<driver_name>", 'show_logs', M.show_logs)

    host, port = arguments['--listen'].split(':')
    # app.debug = True
    app.run(host, int(port))
