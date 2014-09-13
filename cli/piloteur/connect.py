#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import subprocess
import os
import time

from .util import open_ssh, SSH_KEY

def connect(node_id, config, env):
    client = open_ssh("bridge", config)
    cmd = 'egrep -H "^{}$" ~piloteur/ssh_ports/*'.format(node_id)
    stdin, stdout, stderr = client.exec_command(cmd)

    out = stdout.read().strip()
    if out == "":
        logging.error("Node ID not found on the bridge")
        return 1

    port = out.split(':')[0].rsplit('/')[-1]
    client.close()

    p = subprocess.Popen(["ssh", "-T", "-L", "%s:127.0.0.1:%s" % (port, port),
        "-o StrictHostKeyChecking=no", "-i", SSH_KEY,
        "admin@%s" % config["nodes"]["bridge"]],
        stdout=open(os.devnull), stderr=open(os.devnull), stdin=subprocess.PIPE)

    time.sleep(1)
    subprocess.call(["ssh", "-p%s" % port, "-i", SSH_KEY,
        "-o StrictHostKeyChecking=no", "admin@127.0.0.1"])

    p.terminate()

    return 0
