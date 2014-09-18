#!/usr/bin/env python

import sys
import os.path
import urllib2

HOME = sys.argv[1]
ADDR = sys.argv[2]

PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"
TOKEN = "###PILOTEUR-MAGIC-TOKEN###"

with open(os.path.join(HOME, '.config-token')) as f:
    TOKEN = f.read().strip()

with open(PATH) as f:
    sys_cfg = f.read()
    sys_cfg = sys_cfg.split(TOKEN)[0].strip()
    sys_cfg += '\n\n' + TOKEN + '\n\n'

cfg = urllib2.urlopen("%s/v1/%s/wlan.cfg").read()

with open(PATH, 'w') as f:
    f.write(sys_cfg + cfg)
