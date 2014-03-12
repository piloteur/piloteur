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
import email.utils
import urllib2
import itertools

import socket
socket.setdefaulttimeout(60)

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
    return os.path.realpath(device)


class Syncer():
    def __init__(self, config):
        self.config = config

        logging.basicConfig(format=self.config['log_format'])
        self.log = logging.getLogger('HUB')
        if os.environ.get('DEBUG'):
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        self.log.debug('Loaded config: %s', self.config)

        with open(os.path.expanduser('~/.hub-id')) as f:
            self.HUB_ID = f.read().strip()

        self.DATA_PATH = os.path.expanduser(self.config['data_path'])
        self.LOGS_PATH = os.path.expanduser(self.config['logs_path'])

        self.REMOTE_DATA_PATH = os.path.join('data', self.HUB_ID)
        self.REMOTE_LOGS_PATH = os.path.join('logs', self.HUB_ID)

        self.LOG_HOUR = datetime.datetime.now().strftime('%Y-%m-%d-%H')

        self.KEYFILE_PATH = os.path.expanduser(self.config['keyfile_path'])

    # def run_remote_command(self, command):
    #     ssh_cmd = ["ssh", "-i", self.KEYFILE_PATH]
    #     ssh_cmd += ["%s@%s" % (self.config['remoteuser'], self.config['remotehost'])]
    #     ssh_cmd += [command]

    #     self.log.info('Running remote command "%s"', command)
    #     subprocess.check_call(ssh_cmd)

    def run(self):
        self.log.info('---')
        self.start_time = time.time()

        try:
            # Maybe running rsync two times might have to be reconsidered
            success = self.sync(self.DATA_PATH, self.REMOTE_DATA_PATH)
            success &= self.sync(self.LOGS_PATH, self.REMOTE_LOGS_PATH)
        except:
            traceback.print_exc()
        else:
            if success: self.after_success()

        self.monitor()
        self.timesync()

    def sync(self, local_path, remote_path):
        rsync_cmd = ["rsync", "-avz", "--append"]
        rsync_cmd += ["--timeout", "30"]
        rsync_cmd += ["--chmod", self.config['remote_chmod']]
        rsync_cmd += ["-e", 'ssh -i %s' % self.KEYFILE_PATH]

        rsync_cmd += [local_path]
        rsync_cmd += ["%s@%s:%s" % (self.config['remoteuser'],
            self.config['remotehost'], remote_path)]

        self.log.debug('rsync command line: %s', rsync_cmd)

        self.log.info('Starting rsync %s -> %s...', local_path, remote_path)
        ecode = subprocess.call(rsync_cmd)
        if ecode == 0:
            self.log.info('rsync finished successfully.')
            return True
        else:
            self.log.error('rsync exited with status %i', ecode)
            return False

    def after_success(self):
        data_files = listfiles(self.DATA_PATH)
        groupfunc = lambda x: os.path.basename(x).split('-')[0]
        data_files = sorted(data_files, key=groupfunc)
        for k, g in itertools.groupby(data_files, groupfunc):
            self.prune_old(list(g))

        self.prune_old(listfiles(self.LOGS_PATH))
        log_modules_folders = listdirs(self.LOGS_PATH)
        for log_modules_folder in log_modules_folders:
            self.prune_old(listfiles(log_modules_folder))

    def prune_old(self, files):
        # Please note the (unavoidable?) race condition between
        # os.path.getmtime and os.remove

        files = [(name, os.path.getmtime(name))
            for name in files]
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

    def monitor(self):
        MONITOR_PATH = os.path.join(self.LOGS_PATH, "monitor/monitor-log.%s.json" % self.LOG_HOUR)

        data = {}

        data["uptime"] = uptime.uptime()
        data["timestamp"] = datetime.datetime.now().isoformat()
        data["cpu_percent"] = psutil.cpu_percent(0)
        data["free_memory"] = psutil.virtual_memory().available
        data["free_disk"] = psutil.disk_usage(self.DATA_PATH).free

        device = os.path.basename(get_device(self.DATA_PATH))
        iostat = psutil.disk_io_counters(perdisk=True)[device]
        data["iostat"] = {
            "read_bytes": iostat.read_bytes,
            "write_bytes": iostat.write_bytes,
            "read_count": iostat.read_count,
            "write_count": iostat.write_count
        }

        self.log.debug(data)

        with open(MONITOR_PATH, 'a') as f:
            json.dump(data, f, sort_keys=True)
            f.write('\n')

    def timesync(self):
        TIMESYNC_PATH = os.path.join(self.LOGS_PATH, "timesync/timesync-log.%s.csv" % self.LOG_HOUR)

        remote = datetime.datetime(*email.utils.parsedate(
            urllib2.urlopen('http://google.com').info().getheader('Date'))[:6])
        local = datetime.datetime.utcnow()

        with open(TIMESYNC_PATH, 'a') as f:
            f.write('%s,%s,%f\n' %(local.isoformat(), remote.isoformat(),
                (remote - local).total_seconds()))



def main():
    config = json.loads(subprocess.check_output('./config.py'))

    s = Syncer(config)
    s.run()

if __name__ == '__main__':
    main()
