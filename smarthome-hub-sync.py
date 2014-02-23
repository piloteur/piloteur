import json
import logging
import subprocess
import os.path

class Syncer():
    def __init__(self):
        FORMAT = '[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s'
        logging.basicConfig(format=FORMAT)
        self.log = logging.getLogger('HUB')
        self.log.setLevel(logging.INFO)

        with open('config.json') as f:
            self.config = json.load(f)
        self.log.debug('Loaded config: %s', self.config)

    def run(self):
        rsync_cmd = ["rsync", "-avz", "--append"]
        rsync_cmd += ["-e", 'ssh -i ./smarthome-remote-key']
        rsync_cmd += [os.path.expanduser("~/data/")]
        rsync_cmd += ["%s@%s:/var/smarthome/data/" % (
            self.config['remoteuser'], self.config['remotehost'])]
        self.log.debug('rsync command line: %s', rsync_cmd)

        self.log.info('Starting rsync...')
        ecode = subprocess.call(rsync_cmd)
        if ecode == 0:
            self.log.info('rsync finished successfully.')
        else:
            self.log.error('rsync exited with status %i', ecode)

def main():
    s = Syncer()
    s.run()

if __name__ == '__main__':
    main()
