#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os.path
import json
import subprocess
import sys
import os
import datetime
import calendar

class MetricsCollector():
    def __init__(self):
        with open(os.path.expanduser('~/.hub-id')) as f:
            self.hub_id = f.read().strip()

        self.config = json.loads(subprocess.check_output(os.path.expanduser(
            '~/smarthome-hub-sync/config.py')))

        self.DATA_PATH = os.path.expanduser(self.config['data_path'])
        self.LOGS_PATH = os.path.expanduser(self.config['logs_path'])

    def run(self):
        payload = {
            'hub-id': self.hub_id,
            # 'config': self.config,
            'timestamp': calendar.timegm(datetime.datetime.utcnow().utctimetuple()),
            'last_writes': self._last_writes(),
            'versions': self._versions(),
        }

        return payload

    def _get_file(self, base, name):
        hour = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H')
        filename = os.path.join(base, name % {'hour': hour})

        if not os.path.isfile(filename):
            ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            hour = ago.strftime('%Y-%m-%d-%H')
            filename = os.path.join(base, name % {'hour': hour})

        if not os.path.isfile(filename):
            raise IOError

        return filename

    def _last_writes(self):
        last_writes = {}
        for driver_name in self.config['loaded_drivers']:
            try:
                filename = self._get_file(self.DATA_PATH, driver_name + '-%(hour)s.data')
            except IOError:
                last_writes[driver_name] = 0
                continue
            t = os.path.getmtime(filename)
            last_writes[driver_name] = t
        return last_writes


    def _versions(self):
        try:
            filename = self._get_file(self.LOGS_PATH, 'versions/versions-log.%(hour)s.csv')
        except IOError:
            return None

        with open(filename) as f:
            versions = f.read().strip().split('\n')[-1].split(',')
        return dict(zip((
            "timestamp",
            "ansible",
            "smart-home-config",
            "smarthome-deployment-blobs",
            "smarthome-drivers",
            "smarthome-hub-sync",
            "smarthome-reverse-tunneler",
        ), versions))


if __name__ == '__main__':
    m = MetricsCollector()
    json.dump(m.run(), sys.stdout)
