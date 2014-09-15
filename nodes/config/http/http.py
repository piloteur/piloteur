#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Piloteur config node.

Usage: http.py serve [--listen=<addr>]

Options:
  --listen ADDR  IP and port to bind to [default: 0.0.0.0:8080]
  -h --help      Show this screen.
  --version      Show version.

"""

import json
import os.path
import sys
import hmac
import hashlib
from docopt import docopt
from flask import Flask, Response, abort

PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT)
import config

KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')


def compare_digest(x, y):
    if not (isinstance(x, bytes) and isinstance(y, bytes)):
        raise TypeError("both inputs should be instances of bytes")
    if len(x) != len(y):
        return False
    result = 0
    for a, b in zip(x, y):
        result |= ord(a) ^ ord(b)
    return result == 0


def check_sig(msg, sig):
    with open(KEY_PATH, 'rb') as f:
        key = f.read()

    h = hmac.new(key, msg, hashlib.sha256).hexdigest()

    return compare_digest(h, sig)


class Config():
    def get_config(self, token):
        parts = token.split(',')
        if len(parts) < 2: abort(400)

        UUID = parts[0]
        sig = parts[-1].encode()
        classes = parts[1:-1]

        if not check_sig(','.join(parts[:-1]), sig): abort(403)

        result = config.make_config(UUID, classes)

        result = json.dumps(result, indent=4)
        return Response(result, mimetype='application/json')


if __name__ == '__main__':
    # DIR = os.path.dirname(os.path.abspath(__file__))
    # with open(os.path.expanduser('~/piloteur-config/monitor/config.json')) as f:
    #     config = json.load(f)

    arguments = docopt(__doc__, version='Piloteur config node 0.1')

    C = Config()

    app = Flask(__name__)

    app.add_url_rule("/v1/<token>/config.json", 'get_config', C.get_config)

    host, port = arguments['--listen'].split(':')
    # app.debug = True
    app.run(host, int(port))
