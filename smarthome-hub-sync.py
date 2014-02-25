import json
import logging
import subprocess
import os.path
import os
import operator
import time
import psutil
import uptime
import datetime
import traceback

listdirs = lambda dirname: [os.path.join(dirname, x)
                for x in os.listdir(dirname)
                if os.path.isdir(os.path.join(dirname, x))]

listfiles = lambda dirname: [os.path.join(dirname, x)
                for x in os.listdir(dirname)
                if os.path.isfile(os.path.join(dirname, x))]

def get_device(path):
    output = subprocess.check_output(["df", path])
    device, size, used, available, percent, mountpoint = \
        output.split("\n")[1].split()
    return device


class Syncer():
    TIMESTAMP_PATH = './var/smarthome-hub-sync.timestamp'
    LOCAL_PATH = os.path.expanduser("~/data/")
    KEYFILE_PATH = './smarthome-remote-key'
    MONITORING_PATH = './logs/smarthome-hub-sync.json'

    def __init__(self):
        FORMAT = '[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s'
        logging.basicConfig(format=FORMAT)
        self.log = logging.getLogger('HUB')
        if os.environ.get('DEBUG'):
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        with open('config.json') as f:
            self.config = json.load(f)
        self.log.debug('Loaded config: %s', self.config)

    def run(self):
        self.start_time = time.time()

        try:
            success = self.sync()
        except:
            traceback.print_exc()
        else:
            if success: self.after_success()

        self.finish()

    def sync(self):
        rsync_cmd = ["rsync", "-avz", "--append"]
        rsync_cmd += ["--timeout", "5"]
        rsync_cmd += ["-e", 'ssh -i %s' % self.KEYFILE_PATH]
        rsync_cmd += [self.LOCAL_PATH]
        rsync_cmd += ["%s@%s:%s" % (self.config['remoteuser'],
            self.config['remotehost'], self.config['remotepath'])]
        self.log.debug('rsync command line: %s', rsync_cmd)

        self.log.info('Starting rsync...')
        ecode = subprocess.call(rsync_cmd)
        if ecode == 0:
            self.log.info('rsync finished successfully.')
            return True
        else:
            self.log.error('rsync exited with status %i', ecode)
            return False

    def after_success(self):
        last_sync = 0
        if os.path.isfile(self.TIMESTAMP_PATH):
            with open(self.TIMESTAMP_PATH) as f:
                content = f.read().strip()
            if content.isdigit():
                last_sync = int(content)

        sensor_kind_folders = listdirs(self.LOCAL_PATH)
        for sensor_kind_folder in sensor_kind_folders:
            sensor_folders = listdirs(sensor_kind_folder)
            for sensor_folder in sensor_folders:
                self.prune_old(sensor_folder, last_sync)

        with open(self.TIMESTAMP_PATH, 'w') as f:
            print >> f, int(self.start_time)

    def prune_old(self, sensor_folder, last_sync):
        files = [(name, os.path.getmtime(name))
            for name in listfiles(sensor_folder)]
        files.sort(key=operator.itemgetter(1), reverse=True)

        self.log.debug(files)

        # Save the two most recent files
        files = files[2:]

        # Filter out still unsynced files
        files = [(f, t) for f, t in files if t < self.start_time]

        for f, t in files:
            self.log.info('Pruning old file %s modified on %f'
                % (f, t))
            os.remove(f)

    def finish(self):
        data = {}

        data["uptime"] = uptime.uptime()
        data["timestamp"] = datetime.datetime.now().isoformat()
        data["cpu_percent"] = psutil.cpu_percent(0)
        data["free_memory"] = psutil.virtual_memory().available
        data["free_disk"] = psutil.disk_usage(self.LOCAL_PATH).free

        device = os.path.basename(get_device(self.LOCAL_PATH))
        iostat = psutil.disk_io_counters(perdisk=True)[device]
        data["iostat"] = {
            "read_bytes": iostat.read_bytes,
            "write_bytes": iostat.write_bytes,
            "read_count": iostat.read_count,
            "write_count": iostat.write_count
        }

        self.log.debug(data)

        with open(self.MONITORING_PATH, 'a') as f:
            json.dump(data, f, sort_keys=True)
            f.write('\n')



def main():
    s = Syncer()
    s.run()

if __name__ == '__main__':
    main()
