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
import sys
import select

DIR = os.path.dirname(os.path.realpath(__file__))
CODE = os.path.join(DIR, '..', '..')
DEPLOYMENT = os.path.join(CODE, 'deployment')
SSH_KEY = os.path.join(CODE, 'keys', 'piloteur-admin')

def dep_call(command, config, env, capture_output=True):
    cmd_env = os.environ.copy()
    cmd_env.update(env)
    cmd_env["PATH"] = (os.path.join(config["paths"]["virtualenv"], "bin")
        + ":" + cmd_env["PATH"])
    if capture_output:
        return subprocess.check_output(command, env=cmd_env, cwd=DEPLOYMENT)
    else:
        return subprocess.check_call(command, env=cmd_env, cwd=DEPLOYMENT)

def open_ssh(node_name, config):
    if node_name == "monitor":
        host, user = config["nodes"]["monitor"], "admin"
    elif node_name == "bridge":
        host, user = config["nodes"]["bridge"], "admin"
    elif node_name == "config":
        host, user = config["nodes"]["config"], "admin"
    elif node_name == "github":
        host, user = "github.com", "git"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, 22, user, key_filename=SSH_KEY)
    return client

def init_nexus(config):
    nexus_config = {
        "sync_nodes": config["nodes"]["sync"],
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
        sys.exit(1)

    port = out.split(':')[0].rsplit('/')[-1]
    client.close()

    p = subprocess.Popen(["ssh", "-v", "-T", "-L", "%s:127.0.0.1:%s" % (port, port),
        "-o StrictHostKeyChecking=no", "-i", SSH_KEY,
        "admin@%s" % config["nodes"]["bridge"]],
        stderr=subprocess.PIPE, stdout=open(os.devnull), stdin=subprocess.PIPE)

    while True:
        line = p.stderr.readline()
        if 'Entering interactive session.' in line:
            break

    return p, port

def call_ansible(arguments, config, env):
    ansible_path = os.path.join(config["paths"]["virtualenv"], "bin", "ansible-playbook")
    cmd = [ansible_path]
    cmd.extend(arguments)
    return dep_call(cmd, config, env, capture_output=False)

def redirect_paramiko(stdout, stderr):
    while True:
        if stdout.channel.recv_ready():
            rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
            if len(rl) > 0:
                sys.stdout.write(stdout.channel.recv(1024))
        if stderr.channel.recv_ready():
            rl, wl, xl = select.select([stderr.channel], [], [], 0.0)
            if len(rl) > 0:
                sys.stderr.write(stderr.channel.recv(1024))
        if stdout.channel.exit_status_ready():
            break

    return stdout.channel.recv_exit_status()
