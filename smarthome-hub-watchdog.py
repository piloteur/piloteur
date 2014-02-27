import json
import logging
import os.path
import os

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

        self.WATCH_PATH = os.path.expanduser(self.config['watchdog_path'])

    def run(self):
        self.log.info('Watchdog starting...')

        pass

def main():
    with open('config.json') as f:
        config = json.load(f)

    s = Watchdog(config)
    s.run()

if __name__ == '__main__':
    main()
