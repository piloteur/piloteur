#!/usr/bin/env python2.7

import os, os.path

hostname = raw_input()

list_filenames = lambda dirname: [x for x in os.listdir(dirname)
                    if os.path.isfile(os.path.join(dirname, x))]

base_port = 40000
ports_folder = os.path.expanduser("~/ssh_ports/")

while True:
    port = next(str(n) for n in range(base_port, 65535)
                if not str(n) in list_filenames(ports_folder))

    try:
        fd = os.open(os.path.join(ports_folder, port), os.O_RDWR|os.O_CREAT|os.O_EXCL, 0644)
    except OSError:
        continue
    else:
        break

os.write(fd, hostname)
os.close(fd)

print port
