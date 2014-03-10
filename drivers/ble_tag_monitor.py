import subprocess
import sys
import json
import time

class BLE_driver():
    def __init__(self):
        self.lescan_pid = None

    def run(self):
        while True:
            self.reset()
            self.start_lescan()
            print >> sys.stderr, 'ERROR: lescan quit, restarting'

    def start_lescan(self):
        p = subprocess.Popen(['sudo', 'lescan'], stdout=subprocess.PIPE)
        print >> sys.stderr, 'started lescan, pid %s' % p.pid
        self.lescan_pid = p.pid
        while True:
            line = p.stdout.readline().rstrip()
            if not line: break
            data = json.loads(line)
            print '%(timestamp)s,%(bdaddr)s,%(rssi)s' % data

    def reset(self):
        lsusb = subprocess.check_output("lsusb").split('\n')
        blue = next(line for line in lsusb if 'bluetooth' in line.lower()) # XXX
        bus, device = blue[4:7], blue[15:18]
        print >> sys.stderr, 'resetting usb %s %s' % (bus, device)
        subprocess.check_call(["sudo", "usbreset", "/dev/bus/usb/%s/%s" % (bus, device)],
            stdout=sys.stderr)
        time.sleep(2)

def main():
    b = BLE_driver()
    b.run()

if __name__ == '__main__':
    main()
