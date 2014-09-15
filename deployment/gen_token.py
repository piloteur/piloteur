#!/usr/bin/env python
#-*- coding:utf-8 -*-

import hmac
import hashlib
import os.path
import sys

DIR = os.path.dirname(os.path.realpath(__file__))
KEY_PATH = os.path.join(DIR, '..', 'keys', 'piloteur-admin')

with open(KEY_PATH, 'rb') as f:
    key = f.read()

h = hmac.new(key, sys.argv[1], hashlib.sha256).hexdigest()

print sys.argv[1] + ',' + h
