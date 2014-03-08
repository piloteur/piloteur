import os
import subprocess
import imp
import signal
import time
import psutil
import hashlib

from .utils import (
    running_python_scripts
)

class DriversManager():
    def __init__(self, watchdog):
        self.watchdog = watchdog
        self.config = watchdog.config
        self.log = watchdog.log

        # TODO: un-hardcode this repo path
        self.DRIVERS_PATH = os.path.expanduser('~/smarthome-drivers/drivers')

        self.DRIVER_WRAPPER = os.path.abspath('smarthome-hub-watchdog/driver-wrapper.sh')

        self.FINGERPRINT_PATH = os.path.expanduser('~/.version_fingerprint')

    def run(self):
        self.check_changes()
        self.watch()

    def check_changes(self):
        hub_head = subprocess.check_output(["git", "rev-parse", "HEAD"],
            cwd=os.path.expanduser('~/smarthome-hub-sync'))
        config = hashlib.md5(subprocess.check_output(["./config.py"],
            cwd=os.path.expanduser('~/smarthome-hub-sync'))).hexdigest()

        fingerprint = hub_head + '\n' + config

        if os.path.isfile(self.FINGERPRINT_PATH):
            with open(self.FINGERPRINT_PATH) as f:
                old_fingerprint = f.read()
        else:
            old_fingerprint = ''

        if fingerprint != old_fingerprint:
            self.terminate_all()

        with open(self.FINGERPRINT_PATH, 'w') as f:
            f.write(fingerprint)

    def terminate_all(self):
        """
        This will terminate all the running modules named like a module in DRIVERS_PATH
        """
        for module_name, pid in running_python_scripts(True):
            try:
                imp.find_module(module_name, [self.DRIVERS_PATH])
            except ImportError:
                continue

            self.log.info('terminating driver %s' % module_name)
            self.terminate(pid)

    def terminate_name(self, name):
        running_modules = dict(running_python_scripts(True))
        if not name in running_modules:
            self.log.warning('got asked to terminate module %s, but it is not running' % name)
            return

        self.log.info('terminating driver %s' % name)
        self.terminate(running_modules[name])

    def terminate(self, pid):
        os.kill(pid, signal.SIGTERM)
        if not psutil.pid_exists(pid): return
        time.sleep(1)
        if not psutil.pid_exists(pid): return
        time.sleep(2)
        if psutil.pid_exists(pid):
            self.log.warning('pid %s failed to terminate in 3s, killing' % pid)
            os.kill(pid, signal.SIGKILL)

    def watch(self):
        running_modules = set(n for n, p in running_python_scripts(True))
        self.log.debug(running_modules)

        for driver_name in self.config['loaded_drivers']:
            try:
                imp.find_module(driver_name, [self.DRIVERS_PATH])
            except ImportError:
                self.log.error('driver %s not found' % driver_name)
                continue

            if driver_name not in running_modules:
                self.log.error('%s is not running' % driver_name)

                p = subprocess.Popen(
                    [self.DRIVER_WRAPPER, driver_name], close_fds=True)
                self.log.info('restarted %s with pid %i', driver_name, p.pid)
