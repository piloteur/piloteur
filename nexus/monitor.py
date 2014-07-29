from __future__ import absolute_import, print_function, division, unicode_literals

import subprocess
import os.path
import json
import arrow
import datetime
import collections
import paramiko

from . import RED, YELLOW, GREEN, list_hub_ids, data_timestamp
from . import private

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

def fetch_data(hub_id):
    private.set_hub_id(hub_id)

    if hub_id not in list_hub_ids():
        return NodeData(hub_id=hub_id, error="Hub ID not found.")

    classes_log = private.fetch_system_logs("classes")
    if not classes_log:
        return NodeData(hub_id=hub_id, error="Missing classes data.")
    remote_hub_id = classes_log.split(',')[0]
    if not remote_hub_id == hub_id:
        return NodeData(hub_id=hub_id, error="Mismatching hub_id?!")
    classes = classes_log.split(',')[1:]

    config_cmd = [os.path.expanduser("~/smarthome-hub-sync/config.py")]  # TODO
    config_cmd.append(hub_id)
    config_cmd.extend(classes)
    node_config = json.loads(subprocess.check_output(config_cmd))

    timesync_log = private.fetch_system_logs("timesync")
    if not timesync_log:
        return NodeData(hub_id=hub_id, error="Missing timesync data.")
    timestamp = arrow.get(timesync_log.split(',')[0])

    iwconfig_log = private.fetch_system_logs("iwconfig")
    if not iwconfig_log:
        return NodeData(hub_id=hub_id, error="Missing iwconfig data.")
    wifi_quality = iwconfig_log.split(',')[1]
    if wifi_quality == 'N/A': wifi_quality = None
    else: wifi_quality = int(wifi_quality)

    versions_log = private.fetch_system_logs("versions")
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
        t = data_timestamp(driver_name)
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

def assess_data(data):
    if data.error:
        return NodeResult(
            hub_id=data.hub_id,
            hub_health=RED,
            error=data.error,
        )

    drivers = []
    versions = []

    hub_health = GREEN
    error_message = ''


    ########################################################################
    # DRIVERS                                                              #
    ########################################################################
    for driver_name, last_write in sorted(data.last_writes.items()):
        health = GREEN
        if (data.timestamp - last_write) > YELLOW_LIMIT:
            health = YELLOW
        if (data.timestamp - last_write) > RED_LIMIT:
            health = RED

        if health != GREEN:
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
    health = GREEN
    ansible = data.versions['ansible']
    if ansible != 'ansible 1.5.3':  # TODO unhardcode?
        health = RED
        error_message += 'Old Ansible version. '
    hub_health = max(hub_health, health)
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
        hub_health = max(hub_health, YELLOW)
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
