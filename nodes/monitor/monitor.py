from __future__ import absolute_import, print_function, division, unicode_literals

import subprocess
import os.path
import json
import arrow
import collections
import paramiko
import sys
import importlib
import traceback
import datetime

from nexus import RED, YELLOW, GREEN, list_node_ids
import nexus.private

def void_namedtuple(ntuple):
    void = ntuple._make([None] * len(ntuple._fields))
    def new(**kwargs):
        return void._replace(**kwargs)
    return new

NodeData = void_namedtuple(collections.namedtuple('NodeData',
    ['node_id', 'classes', 'timestamp', 'versions', 'wifi_quality', 'error', 'config']))
NodeResult = void_namedtuple(collections.namedtuple('NodeResult',
    ['node_id', 'classes', 'timestamp', 'versions', 'wifi_quality', 'error', 'summary', 'node_health', 'drivers']))


def get_bridge_connections(bridge_info):
    username, hostname, port, folder = bridge_info

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username)

    cmd = "grep -h . {}*".format(folder)
    stdin, stdout, stderr = client.exec_command(cmd)
    return [n.strip() for n in stdout.readlines()]

def fetch_data(node_id, config):
    nexus.private.set_node_id(node_id)

    if node_id not in list_node_ids():
        return NodeData(node_id=node_id, error="Node ID not found.")

    classes_log = nexus.private.fetch_system_logs("classes")
    if not classes_log:
        return NodeData(node_id=node_id, error="Missing classes data.")
    remote_node_id = classes_log.split(',')[0]
    if not remote_node_id == node_id:
        return NodeData(node_id=node_id, error="Mismatching node_id?!")
    classes = classes_log.split(',')[1:]

    config_cmd = [os.path.expanduser("~/piloteur-code/nodes/endpoint/config.py")]
    config_cmd.append(node_id)
    config_cmd.extend(classes)
    node_config = json.loads(subprocess.check_output(config_cmd))

    timestamp = nexus.get_timestamp()
    if timestamp is None:
        return NodeData(node_id=node_id, error="Missing timesync data.")
    timestamp = arrow.get(timestamp)

    iwconfig_log = nexus.private.fetch_system_logs("iwconfig")
    if not iwconfig_log:
        return NodeData(node_id=node_id, error="Missing iwconfig data.")
    wifi_quality = iwconfig_log.split(',')[1]
    if wifi_quality == 'N/A': wifi_quality = None
    else: wifi_quality = int(wifi_quality)

    versions_log = nexus.private.fetch_system_logs("versions")
    if not versions_log:
        return NodeData(node_id=node_id, error="Missing versions data.")
    versions = versions_log.split(',')
    versions = dict(zip((
        "timestamp",
        "ansible",
        "piloteur-code",
        "piloteur-config",
        "piloteur-blobs",
    ), versions))

    return NodeData(node_id=node_id,
                    classes=classes,
                    config=node_config,
                    timestamp=timestamp,
                    versions=versions,
                    wifi_quality=wifi_quality)

def assess_data(data, config):
    if data.error:
        return NodeResult(
            node_id=data.node_id,
            node_health=RED,
            error=data.error,
        )

    drivers_path = os.path.expanduser("~/piloteur-code/drivers")
    if not drivers_path in sys.path: sys.path.append(drivers_path)
    from checks.common import data_freshness_check

    node_health = GREEN
    error_message = ''


    ########################################################################
    # DRIVERS                                                              #
    ########################################################################
    drivers = []
    for driver_name in sorted(data.config['loaded_drivers']):
        try:
            module = importlib.import_module('checks.' + driver_name)
            check = module.check
        except ImportError:
            # TODO: communicate somehow that we are fallbacking
            red_limit = datetime.timedelta(hours=1)
            check = data_freshness_check(driver_name, red_limit)

        try:
            nexus.private.set_node_id(data.node_id)  # TODO but better safe than sorry
            res = check(data.node_id)
        except:
            exc_msg = traceback.format_exception_only(*sys.exc_info()[:2])[-1]
            return NodeResult(
                node_id=data.node_id,
                node_health=RED,
                error=exc_msg,
            )

        # TODO handle multiple values in the res list
        health, message = res[0]['status'], res[0]['note']

        if health != GREEN:
            error_message += '"{}": {}. '.format(driver_name, message)
        node_health = max(node_health, health)
        drivers.append((driver_name, message, health))

    ########################################################################
    # VERSIONS                                                             #
    ########################################################################
    versions = []
    health = GREEN
    ansible = data.versions['ansible']
    if ansible != 'ansible 1.5.3':  # TODO unhardcode?
        health = RED
        error_message += 'Old Ansible version. '
    node_health = max(node_health, health)
    versions.append(('ansible', ansible, 'ansible 1.5.3', health))

    del data.versions['timestamp']
    del data.versions['ansible']

    for repo, commit in data.versions.items():
        # TODO get repo last commit and check how old is this
        versions.append((repo, commit[:7], '', GREEN))

    ########################################################################
    # WI-FI QUALITY                                                        #
    ########################################################################
    if data.wifi_quality and data.wifi_quality < 30:
        node_health = max(node_health, YELLOW)
        error_message += 'Weak Wi-Fi signal. '


    return NodeResult(
        drivers=drivers,
        timestamp=data.timestamp.format('YYYY-MM-DD HH:mm:ss ZZ'),
        node_id=data.node_id,
        node_health=node_health,
        versions=versions,
        classes=data.classes,
        wifi_quality=data.wifi_quality,
        summary=error_message,
    )
