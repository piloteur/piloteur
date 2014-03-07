import psutil
import fcntl
import struct
import time
import os
import os.path
import subprocess
import sys
import socket

def running_python_scripts(modules=False):
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
                    if not modules:
                        yield os.path.normpath(os.path.join(cwd, path))
                break
            if arg == '-m':
                if len(p.cmdline) > n+1 and p.cmdline[n+1] != '-':
                    module_name = p.cmdline[n+1]
                    if modules: yield module_name
                break
            if arg in ('-c', '-'): break
            if arg.startswith('-'): continue
            if not modules:
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
