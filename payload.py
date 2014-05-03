#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os.path
import json
import subprocess
import sys
import os
import datetime
import calendar

payload = {}

with open(os.path.expanduser('~/.hub-id')) as f:
    payload['hub-id'] = f.read().strip()

config = json.loads(subprocess.check_output(os.path.expanduser(
    '~/smarthome-hub-sync/config.py')))
# payload['config'] = config

DATA_PATH = os.path.expanduser(config['data_path'])
LOGS_PATH = os.path.expanduser(config['logs_path'])

payload['last_writes'] = {}
for driver_name in config['loaded_drivers']:
    filename = os.path.join(DATA_PATH, '%(name)s-%(hour)s.data')
    hour = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H')
    filename = filename % {'name': driver_name, 'hour': hour}
    if not os.path.isfile(filename):
        ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        hour = ago.strftime('%Y-%m-%d-%H')
        filename = filename % {'name': driver_name, 'hour': hour}
    if not os.path.isfile(filename):
        payload['last_writes'][driver_name] = 0
        continue
    t = os.path.getmtime(filename)
    payload['last_writes'][driver_name] = t

hour = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H')
versions_file = os.path.join(LOGS_PATH, "versions/versions-log.%s.csv" % hour)
if not os.path.isfile(versions_file):
    ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    hour = ago.strftime('%Y-%m-%d-%H')
    versions_file = os.path.join(LOGS_PATH, "versions/versions-log.%s.csv" % hour)
if not os.path.isfile(versions_file):
    payload['versions'] = None
else:
    with open(versions_file) as f:
        versions = f.read().strip().split('\n')[-1].split(',')
    payload['versions'] = dict(zip((
        "timestamp",
        "ansible",
        "smart-home-config",
        "smarthome-deployment-blobs",
        "smarthome-drivers",
        "smarthome-hub-sync",
        "smarthome-reverse-tunneler",
    ), versions))

payload['timestamp'] = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

json.dump(payload, sys.stdout)
