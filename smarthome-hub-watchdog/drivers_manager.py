import os
import subprocess
import imp

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

    def run(self):
        running_modules = set(running_python_scripts(True))
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
