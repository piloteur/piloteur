import json
import logging
import os.path
import os
import psutil
import subprocess

# Note: for a script to be relaunched, it has to be executable, end in
# .py and accept running with working directory ~. The watchdog has to
# run as the same user as the script. Please consider python-daemon.

def running_python_scripts():
    for p in psutil.process_iter():
        if not p.cmdline: continue
        if not os.path.basename(p.cmdline[0]).startswith('python'):
            continue
        try: cwd = p.getcwd()
        except psutil._error.AccessDenied: continue
        for n, arg in enumerate(p.cmdline[1:]):
            if arg == '--':
                if len(p.cmdline) > n+1 and p.cmdline[n+1] != '-':
                    path = p.cmdline[n+1]
                    yield os.path.normpath(os.path.join(cwd, path))
                break
            if arg in ('-c', '-m', '-'): break
            if arg.startswith('-'): continue
            yield os.path.normpath(os.path.join(cwd, arg))
            break

listfiles = lambda dirname: [os.path.join(dirname, x)
                for x in os.listdir(dirname)
                if os.path.isfile(os.path.join(dirname, x))]

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

        watched_scripts = set(f for f in listfiles(self.WATCH_PATH)
            if f.endswith('.py') and os.access(f, os.X_OK))
        running_scripts = set(running_python_scripts())

        self.log.debug(watched_scripts)
        self.log.debug(running_scripts)

        for failed in watched_scripts - running_scripts:
            self.log.error('%s is not running' % failed)

            p = subprocess.Popen(failed, close_fds=True,
                cwd=os.path.expanduser('~'))
            self.log.info('restarted %s with pid %i', failed, p.pid)

def main():
    with open('config.json') as f:
        config = json.load(f)

    s = Watchdog(config)
    s.run()

if __name__ == '__main__':
    main()
