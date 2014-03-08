import json
import logging
import os.path
import os
import subprocess
import socket
import sys

socket.setdefaulttimeout(60)

from .network_monitor import NetworkMonitor
from .drivers_manager import DriversManager
from .utils import (
    running_python_scripts,
    listfiles
)


class Watchdog():
    def __init__(self, config):
        self.config = config

        logging.basicConfig(format=self.config['log_format'])
        self.log = logging.getLogger('WATCH')
        if os.environ.get('DEBUG'):
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        self.log.debug('Loaded config: %s', self.config)

        self.network_monitor = NetworkMonitor(self)
        self.drivers_manager = DriversManager(self)

    def run(self):
        self.log.info('Watchdog starting...')

        self.monitor_old_services()
        self.drivers_manager.run()

        if self.network_monitor.run():
            sys.exit(1)


    def monitor_old_services(self):
        # Note: for a script to be relaunched, it has to be executable, end in
        # .py and accept running with working directory ~. The watchdog has to
        # run as the same user as the script. Please consider python-daemon.

        WATCH_PATH = os.path.expanduser(self.config['watchdog_path'])

        watched_scripts = set(f for f in listfiles(WATCH_PATH)
            if f.endswith('.py') and os.access(f, os.X_OK))
        running_scripts = set(n for n, p in running_python_scripts())

        self.log.debug(watched_scripts)
        self.log.debug(running_scripts)

        for failed in watched_scripts - running_scripts:
            self.log.error('%s is not running' % failed)

            p = subprocess.Popen(failed, close_fds=True,
                cwd=os.path.expanduser('~'))
            self.log.info('restarted %s with pid %i', failed, p.pid)


def main():
    config = json.loads(subprocess.check_output('./config.py'))

    s = Watchdog(config)
    s.run()

if __name__ == '__main__':
    main()
