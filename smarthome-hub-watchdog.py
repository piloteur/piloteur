import json
import logging
import os.path
import os
import psutil
import subprocess
import socket
import traceback
import fcntl
import struct
import netifaces
import sys
import time

# Note: for a script to be relaunched, it has to be executable, end in
# .py and accept running with working directory ~. The watchdog has to
# run as the same user as the script. Please consider python-daemon.

socket.setdefaulttimeout(60)

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

def is_interface_up(ifname):
    SIOCGIFFLAGS = 0x8913
    null256 = '\0'*256
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    result = fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifname + null256)
    flags, = struct.unpack('H', result[16:18])
    up = flags & 1
    return up

def traceroute(host):
    p = subprocess.Popen(["traceroute", host], stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return p.communicate()[0]

def reboot():
    command = ["sudo", "shutdown", "-r", "now"]
    subprocess.Popen(command)
    sys.exit(2)

def local_network_reset():
    interface_reset()
    subprocess.call(['sudo', 'google-dns'])

def interface_reset():
    for iface in ('eth0', 'wlan0'):
        subprocess.call(['sudo', 'ifdown', iface])
        time.sleep(1)
        subprocess.call(['sudo', 'ifup', iface])
        time.sleep(15)


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
        self.STRIKES_PATH = os.path.expanduser('~/network_strikes')

    def run(self):
        self.log.info('Watchdog starting...')

        self.monitor_services()

        if self.monitor_network():
            self.reset_strikes()
        else:
            sys.exit(1)

    def monitor_services(self):
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

    REMOTE_FAILURE = 'REMOTE_FAILURE'
    DNS_FAILURE = 'DNS_FAILURE'
    CONN_FAILURE = 'CONN_FAILURE'
    IFACE_FAILURE = 'IFACE_FAILURE'
    def monitor_network(self):
        try:
            s = socket.create_connection((self.config['remotehost'], 22), 5)
            banner = s.recv(256)
            s.close()
        except socket.error as e:
            error = traceback.format_exception_only(type(e), e)[-1].strip()
            self.log.error('remote endpoint unreachable: %s' % error)
        else:
            if not banner.startswith('SSH'):
                self.log.error('remote endpoint misbehaved, sent: %s' % banner)
                self.report_failure(self.REMOTE_FAILURE)
                return False
            return True # all good!

        try:
            s = socket.create_connection(('google.com', 80), 10)
            s.send('GET /\n\n')
            s.recv(65535)
            s.close()
        except socket.error as e:
            error = traceback.format_exception_only(type(e), e)[-1].strip()
            self.log.error('google.com unreachable: %s' % error)
        else:
            # if this works but we reached this far, it's the remotehost
            self.report_failure(self.REMOTE_FAILURE)
            return False

        try:
            s = socket.create_connection(('173.194.116.0', 80), 30)
            s.send('GET /\n\n')
            s.recv(65535)
            s.close()
        except socket.error as e:
            error = traceback.format_exception_only(type(e), e)[-1].strip()
            self.log.error('173.194.116.0 unreachable: %s' % error)
        else:
            # if this works but we reached this far, it's the DNS
            self.report_failure(self.DNS_FAILURE)
            return False

        interfaces = list((iface, is_interface_up(iface))
            for iface in netifaces.interfaces()
            if any(iface.startswith(prefix)
                for prefix in ('eth', 'wlan', 'hci')))

        if len(interfaces) == 0:
            self.log.error('no eth*, wlan*, hci* interfaces configured')
            self.report_failure(self.IFACE_FAILURE)
            return False

        interfaces_down = list(iface for iface, up in interfaces if not up)

        if len(interfaces_down) != 0:
            self.log.error('interface down: %s' % ' '.join(interfaces_down))
            self.report_failure(self.IFACE_FAILURE)
            return False

        # if it's not IFACE_FAILURE but we reached here, it's the connection
        self.report_failure(self.CONN_FAILURE)
        return False

    def report_failure(self, failure):
        self.log.error('reported network failure: %s' % failure)
        self.log.info('\n%s' % traceroute(self.config['remotehost']))

        if failure == self.REMOTE_FAILURE:
            return

        self.record_strike()

        if failure in (self.DNS_FAILURE, self.CONN_FAILURE):
            local_network_reset()

        if failure == self.IFACE_FAILURE:
            interface_reset()

    def reset_strikes(self):
        with open(self.STRIKES_PATH, 'w') as f:
            f.write('%i:%i' % (0, self.config['min_network_strikes_limit']))

    def record_strike(self):
        strikes, strikes_limit = 0, 10
        if os.path.isfile(self.STRIKES_PATH):
            with open(self.STRIKES_PATH) as f:
                content = f.read().strip()
            if ':' in content and content.replace(':', '', 1).isdigit():
                strikes, strikes_limit = map(int, content.split(':'))

        strikes += 1

        if strikes == strikes_limit:
            if strikes_limit < self.config['max_network_strikes_limit']:
                strikes_limit += 10

            with open(self.STRIKES_PATH, 'w') as f:
                f.write('%i:%i' % (0, strikes_limit))

            self.log.error('strikes_limit reached, rebooting...')
            self.log.info('new strikes_limit: %i' % strikes_limit)

            reboot()

        self.log.info('strikes:%i strikes_limit:%i' % (strikes, strikes_limit))
        with open(self.STRIKES_PATH, 'w') as f:
            f.write('%i:%i' % (strikes, strikes_limit))


def main():
    config = json.loads(subprocess.check_output('./config.sh'))

    s = Watchdog(config)
    s.run()

if __name__ == '__main__':
    main()
