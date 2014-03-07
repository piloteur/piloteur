import os
import subprocess

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

    def run(self):
        running_scripts = running_python_scripts()
        self.log.debug(running_scripts)

        for driver_name in self.config['loaded_drivers']:
            driver_path = os.path.join(self.DRIVERS_PATH, driver_name,
                '__main__.py')

            if not os.path.isfile(driver_path):
                self.log.error('driver %s not found' % driver_name)
                continue

            if driver_path not in running_scripts:
                self.log.error('%s is not running' % driver_name)

                p = subprocess.Popen(['python', driver_path],
                    close_fds=True, cwd=os.path.expanduser('~'))
                self.log.info('restarted %s with pid %i', driver_name, p.pid)
