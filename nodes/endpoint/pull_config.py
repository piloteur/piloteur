#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os.path
import urllib
import sys

ADDR = sys.argv[1]
PATH = os.path.expanduser('~/config.json')

with open(os.path.expanduser('~/.config-token')) as f:
    TOKEN = f.read().strip()

urllib.urlretrieve("%s/v1/%s/config.json" % (ADDR, TOKEN), PATH)
