#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import subprocess
import os
import os.path
import paramiko
import nexus
import logging
import time

DIR = os.path.dirname(os.path.realpath(__file__))
CODE = os.path.join(DIR, '..', '..')
DEPLOYMENT = os.path.join(CODE, 'deployment')
SSH_KEY = os.path.join(CODE, 'keys', 'piloteur-admin')

def dep_call(command, config, env):
    cmd_env = os.environ.copy()
    cmd_env.update(env)
    cmd_env["PATH"] = (os.path.join(config["paths"]["virtualenv"], "bin")
        + ":" + cmd_env["PATH"])
    return subprocess.check_output(command, env=cmd_env, cwd=DEPLOYMENT)

def open_ssh(node_name, config):
    if node_name == "monitor":
        host, user = config["nodes"]["monitor"], "admin"
    elif node_name == "sync":
        host, user = config["nodes"]["sync"]["host"], config["nodes"]["sync"]["user"]
    elif node_name == "bridge":
        host, user = config["nodes"]["bridge"], "admin"
    elif node_name == "github":
        host, user = "github.com", "git"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, 22, user, key_filename=SSH_KEY)
    return client

def init_nexus(config):
    nexus_config = {
        "data_location": "%s@%s:piloteur/" % (
            config["nodes"]["sync"]["user"], config["nodes"]["sync"]["host"]),
        "ssh_key": SSH_KEY,
        "loglevel": "INFO",
    }

    for _ in range(5):
        try:
            nexus.init(nexus_config)
        except paramiko.SSHException:
            continue
        break
    else:
        logging.error("Failed to reach the sync node")
        exit(1)

def open_bridge(node_id, config):
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
    return p, port
