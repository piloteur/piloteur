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

payload['last_writes'] = {}
for driver_name in config['loaded_drivers']:
    hour = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H')
    filename = os.path.join(DATA_PATH, '%(name)s-%(hour)s.data')
    filename = filename % {'name': driver_name, 'hour': hour}
    t = os.path.getmtime(filename)
    payload['last_writes'][driver_name] = t

payload['timestamp'] = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

json.dump(payload, sys.stdout)
