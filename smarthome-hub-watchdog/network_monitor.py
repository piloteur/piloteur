import traceback
import netifaces
import os
import socket

from .utils import (
    is_interface_up,
    traceroute,
    reboot,
    local_network_reset,
    interface_reset
)

class NetworkMonitor():
    REMOTE_FAILURE = 'REMOTE_FAILURE'
    DNS_FAILURE = 'DNS_FAILURE'
    CONN_FAILURE = 'CONN_FAILURE'
    IFACE_FAILURE = 'IFACE_FAILURE'

    def __init__(self, watchdog):
        self.watchdog = watchdog
        self.config = watchdog.config
        self.log = watchdog.log

        self.STRIKES_PATH = os.path.expanduser('~/network_strikes')

    def run(self):
        if self.monitor_network():
            self.reset_strikes()
        else:
            return 1

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
                self.log.error('remote endpoint misbehaved, sent: %s'
                    % banner)
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
            f.write('%i:%i' % (0, 1))

    def record_strike(self):
        strikes, reboot_num = 0, 1
        if os.path.isfile(self.STRIKES_PATH):
            with open(self.STRIKES_PATH) as f:
                content = f.read().strip()
            if ':' in content and content.replace(':', '', 1).isdigit():
                strikes, reboot_num = map(int, content.split(':'))

        strikes_limit = (self.config['network_strikes_limit_mult']
            * (reboot_num ** 2))
        strikes += 1

        if strikes == strikes_limit:
            with open(self.STRIKES_PATH, 'w') as f:
                f.write('%i:%i' % (0, reboot_num + 1))

            self.log.error('strikes_limit reached, rebooting...')
            self.log.info('%i-th reboot; strikes_limit: %i'
                % (reboot_num, strikes_limit))

            reboot()

        self.log.info('strikes:%i strikes_limit:%i reboot_num:%i'
            % (strikes, strikes_limit, reboot_num))
        with open(self.STRIKES_PATH, 'w') as f:
            f.write('%i:%i' % (strikes, reboot_num))
