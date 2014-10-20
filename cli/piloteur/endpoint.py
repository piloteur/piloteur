#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import paramiko
import subprocess

from .util import open_bridge, SSH_KEY, redirect_paramiko, confirm

def connect(node_id, config, env):
    p, port = open_bridge(node_id, config)

    subprocess.call(["ssh", "-p%s" % port, "-i", SSH_KEY,
        "-o StrictHostKeyChecking=no", "admin@127.0.0.1"])

    p.terminate()

    return 0

def update(node_id, config, env):
    p, port = open_bridge(node_id, config)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("127.0.0.1", int(port), "admin", key_filename=SSH_KEY)

    stdin, stdout, stderr = client.exec_command("~/ansible-pull.sh verbose")
    retcode = redirect_paramiko(stdout, stderr)

    p.terminate()

    return retcode

def decommission(node_id, yes, config, env):
    if not yes and not confirm("Sure you want to disable endpoint %s? "
        "You won't be able to revert this remotely. (y/n) " % node_id): return

    sync(node_id, config, env)

    p, port = open_bridge(node_id, config)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("127.0.0.1", int(port), "admin", key_filename=SSH_KEY)

    stdin, stdout, stderr = client.exec_command("sudo shred /home/piloteur/.ssh/id_rsa /home/admin/.ssh/id_rsa /home/piloteur/.config-token")
    redirect_paramiko(stdout, stderr)

    # TODO: ensure it does not boot again

    stdin, stdout, stderr = client.exec_command("sudo shutdown -h now")
    retcode = redirect_paramiko(stdout, stderr)

    p.terminate()

    return retcode

def batch_decommission(filename, yes, config, env):
    with open(filename) as f:
        for node_id in f:
            node_id = node_id.strip()
            if not node_id: continue
            decommission(node_id, yes, config, env)

def sync(node_id, config, env):
    p, port = open_bridge(node_id, config)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("127.0.0.1", int(port), "admin", key_filename=SSH_KEY)

    stdin, stdout, stderr = client.exec_command(
        "cd /home/piloteur/piloteur-code/nodes/endpoint && "
        "sudo -u piloteur /home/piloteur/ENV/bin/python sync.py")
    retcode = redirect_paramiko(stdout, stderr)

    p.terminate()

    return retcode
