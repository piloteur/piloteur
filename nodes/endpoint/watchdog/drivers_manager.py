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

def parse_ls_tree(stdout):
    result = {}
    if not stdout: return result
    for line in stdout.split('\n'):
        obj, name = line.split('\t')
        if name.endswith('.py'): name = name[:-3]
        result[name] = obj
    return result

class DriversManager():
    def __init__(self, watchdog):
        self.watchdog = watchdog
        self.config = watchdog.config
        self.log = watchdog.log

        self.stopped_drivers = []

        # TODO: un-hardcode this repo path
        self.DRIVERS_PATH = os.path.expanduser('~/piloteur-code/drivers/drivers')

        self.DRIVER_WRAPPER = os.path.abspath('watchdog/driver-wrapper.sh')

        self.GEN_FINGER_PATH = os.path.expanduser('~/.general_fingerprints')
        # self.DRV_FINGER_PATH = os.path.expanduser('~/.drivers_fingerprints')

    def run(self):
        self.check_changes()
        self.watch()

    def check_changes(self):
        self.check_global_changes()
        # self.check_drivers_changes()

    def check_global_changes(self):
        code_head = subprocess.check_output(["git", "rev-parse", "HEAD"],
            cwd=os.path.expanduser('~/piloteur-code'))
        with open(os.path.expanduser('~/config.json')) as f:
            config = hashlib.md5(f.read()).hexdigest()

        fingerprint = code_head + '\n' + config

        if os.path.isfile(self.GEN_FINGER_PATH):
            with open(self.GEN_FINGER_PATH) as f:
                old_fingerprint = f.read()
        else:
            old_fingerprint = ''

        if fingerprint != old_fingerprint:
            self.terminate_all()

        with open(self.GEN_FINGER_PATH, 'w') as f:
            f.write(fingerprint)

    # git ls-tree HEAD
    def check_drivers_changes(self):
        ls_tree = subprocess.check_output(["git", "ls-tree", "HEAD"],
            cwd=self.DRIVERS_PATH).strip()

        if os.path.isfile(self.DRV_FINGER_PATH):
            with open(self.DRV_FINGER_PATH) as f:
                old_ls_tree = f.read()
        else:
            old_ls_tree = ''

        for module_name, pid in running_python_scripts(True):
            if (parse_ls_tree(old_ls_tree).get(module_name) !=
                parse_ls_tree(ls_tree).get(module_name) and
                not module_name in self.stopped_drivers):

                self.log.info('terminating driver %s' % module_name)
                self.stopped_drivers.append(module_name)
                self.terminate(pid)

        with open(self.DRV_FINGER_PATH, 'w') as f:
            f.write(ls_tree)

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
            self.stopped_drivers.append(module_name)
            self.terminate(pid)

    def terminate_name(self, name):
        running_modules = dict(running_python_scripts(True))
        if not name in running_modules:
            self.log.warning('got asked to terminate module %s, but it is not running' % name)
            return

        self.log.info('terminating driver %s' % name)
        self.stopped_drivers.append(name)
        self.terminate(running_modules[name])

    def terminate(self, pid):
        os.kill(pid, signal.SIGTERM)
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
                if driver_name in self.stopped_drivers:
                    self.log.info('restarting %s' % driver_name)
                else:
                    self.log.error('%s is not running' % driver_name)

                find_mod = imp.find_module(driver_name, [self.DRIVERS_PATH])
                cwd = os.path.dirname(find_mod[1]) if find_mod[0] else find_mod[1]
                p = subprocess.Popen(
                    [self.DRIVER_WRAPPER, driver_name, cwd],
                    close_fds=True)
                self.log.info('restarted %s with pid %i', driver_name, p.pid)
