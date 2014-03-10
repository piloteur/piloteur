import subprocess
import sys
import json
import time
import threading
import signal

class BLE_driver():
    def __init__(self):
        self.lescan_pid = None
        self.KILLED_BY_US = False
        self.ALIVE = True

        lsusb = subprocess.check_output("lsusb").split('\n')
        blue = next(line for line in lsusb if 'bluetooth' in line.lower()) # XXX
        self.bus, self.device = blue[4:7], blue[15:18]

    def run(self):
        t = threading.Timer(15, self.monitor); t.daemon = True; t.start()
        while True:
            if not self.KILLED_BY_US: self.reset()
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
        code = subprocess.call(["sudo", "hciconfig", "hci0", "lestates"])
        if code != 0:
            self.KILLED_BY_US = True
            print >> sys.stderr, 'adapter dead, resetting'
            self.reset()

    def reset(self):
        print >> sys.stderr, 'resetting usb %s %s' % (self.bus, self.device)
        subprocess.check_call(["sudo", "usbreset", "/dev/bus/usb/%s/%s" % (self.bus, self.device)],
            stdout=sys.stderr)

    def exit(self, signum=None, frame=None):
        print >> sys.stderr, 'exiting...'
        self.ALIVE = False
        self.reset()
        sys.exit(0)

def main():
    b = BLE_driver()
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
        signal.signal(sig, b.exit)
    b.run()

if __name__ == '__main__':
    main()
