#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import, print_function, division, unicode_literals

import sys
import docopt
import os.path
import json
import logging
import arrow
import paramiko

### Globals

config = None
hub_id = None
log = logging.getLogger('nexus')
sftp = None

### Constants

GREEN = 1
RED = 2
YELLOW = 3

### API functions

def init(new_config):
    global config
    config = new_config

    level = getattr(logging, config.get("loglevel", "INFO"), logging.INFO)
    format = "[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(format=format, level=level)

    if not "data_location" in config or not ':' in config["data_location"] \
                                     or not '@' in config["data_location"]:
        log.error("Mandatory config option data_location not present or malformed.")
        sys.exit(1)

    data_location, path = config["data_location"].rsplit(':', 1)
    port = 22
    if ':' in data_location:
        data_location, port = data_location.split(':')
        port = int(port)
    username, hostname = data_location.split('@')
    key_filename = config.get("ssh_key", None)
    if key_filename:
        key_filename = os.path.expanduser(key_filename)

    log.debug("hostname:%s port:%d username:%s path:%s key_filename:%s",
        hostname, port, username, path, key_filename)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, key_filename=key_filename)

    global sftp
    sftp = client.open_sftp()

def command_line(_name):
    DOC = """
Usage: %s [--config=<path>] <hub-id>

Options:
    --config=<path> The path to SmarthomeX JSON config
                    [default: ~/.smarthomex.json]
    """ % sys.argv[0]

    arguments = docopt.docopt(DOC)

    path = os.path.expanduser(arguments['--config'])
    if not os.path.isfile(path):
        log.error("Config file not existing.")
        sys.exit(1)
    with open(path) as f:
        config = json.load(f)

    init(config)

    if not hasattr(sys.modules[_name], 'PERIOD') or not hasattr(sys.modules[_name], 'check'):
        log.error("PERIOD global or check function not found.")
        sys.exit(1)

    log.info("The check() function would run every... %d seconds", sys.modules[_name].PERIOD)

    global hub_id
    hub_id = arguments["<hub-id>"]

    log.info("Running check() on %s", hub_id)
    results = sys.modules[_name].check(hub_id)

    for r in results:
        t = arrow.get(r["timestamp"]).format('YYYY-MM-DD HH:mm:ss ZZ')
        s = ('GREEN' if r["status"] == GREEN
             else 'YELLOW' if r["status"] == YELLOW
             else 'RED')
        print('[%s] %s: %s ("%s")' % (t, r["name"], s, r["note"]))
