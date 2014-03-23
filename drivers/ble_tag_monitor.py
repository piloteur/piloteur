import subprocess
import sys
import json
import time
import threading
import signal
import os
import re

DEVNULL = open(os.devnull, 'w')

class BLE_driver():
    def __init__(self, lsusb_regex):
        self.lescan_pid = None
        self.KILLED_BY_US = False
        self.ALIVE = True

        for line in subprocess.check_output("lsusb").split('\n'):
            if re.search(lsusb_regex, line):
                self.bus, self.device = line[4:7], line[15:18]
                print >> sys.stderr, 'detected Bluetooth device'
                print >> sys.stderr, line
                break
        else:
            self.bus, self.device = None, None
            print >> sys.stderr, 'WARNING: failed to detect the Bluetooth device'
            print >> sys.stderr, 'this will make us unable to reset it and/or exit cleanly'

    def run(self):
        t = threading.Timer(15, self.monitor); t.daemon = True; t.start()
        while True:
            if not self.KILLED_BY_US: self.reset(force=False)
            time.sleep(2)
            self.start_lescan()
            if not self.ALIVE: break
            print >> sys.stderr, 'ERROR: lescan quit, restarting'

    def start_lescan(self):
        self.KILLED_BY_US = False
        p = subprocess.Popen(['sudo', 'lescan'], stdout=subprocess.PIPE)
        print >> sys.stderr, 'started lescan, pid %s' % p.pid
        self.lescan_pid = p.pid
        while True:
            line = p.stdout.readline().rstrip()
            if not line: break
            data = json.loads(line)
            print '%(timestamp)s,%(bdaddr)s,%(rssi)s' % data

    def monitor(self):
        t = threading.Timer(15, self.monitor); t.daemon = True; t.start()
        code = subprocess.call(["sudo", "hciconfig", "hci0", "lestates"],
            stdout=DEVNULL, stderr=subprocess.STDOUT)
        if code != 0:
            self.KILLED_BY_US = True
            print >> sys.stderr, 'adapter dead, resetting'
            self.reset()

    def reset(self, force=True):
        if not self.device and force:
            print >> sys.stderr, 'ERROR: unable to reset - failed to detect the Bluetooth device'
            sys.exit(1)

        if not self.device:
            return

        print >> sys.stderr, 'resetting usb %s %s' % (self.bus, self.device)
        subprocess.check_call(["sudo", "usbreset", "/dev/bus/usb/%s/%s" % (self.bus, self.device)],
            stdout=sys.stderr)

    def exit(self, signum=None, frame=None):
        print >> sys.stderr, 'exiting...'
        self.ALIVE = False
        self.reset()
        sys.exit(0)

def main():
    config = json.load(sys.stdin)
    regex = config.get('driver_config', {}).get('ble_tag_monitor', {}).get('lsusb_regex')
    if regex is None:
        print >> sys.stderr, 'ERROR: missing config parameters'
        sys.exit(1)

    b = BLE_driver(regex)
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
        signal.signal(sig, b.exit)
    b.run()

if __name__ == '__main__':
    main()
