#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import subprocess
import os
import os.path
import paramiko
import nexus
import logging

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
