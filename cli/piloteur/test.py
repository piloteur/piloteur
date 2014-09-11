#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import subprocess
import os.path
import os

from .util import dep_call, CODE

def test(config, env):
    ### ec2.py
    logging.debug("Testing ec2.py...")
    try:
        dep_call(["./ec2.py", "--list"], config, env)
    except subprocess.CalledProcessError:
        logging.error("ERROR: Error executing ec2.py, check your AWS credentials")
        return 1

    # TODO: test the keypair and the security group

    ### ssh keys
    logging.debug("Testing SSH keys...")
    for name in ("piloteur-admin", "piloteur-devices",
                 "piloteur-admin.pub", "piloteur-devices.pub"):
        if not os.path.exists(os.path.join(CODE, "keys", name)):
            logging.error("The key %s is missing, place it in the keys/ folder", name)
            return 1
    SSH_KEY = os.path.join(CODE, 'keys', 'piloteur-admin')
    code = subprocess.call(["ssh", "-i", SSH_KEY, "git@github.com"],
        stdout=open(os.devnull), stderr=open(os.devnull))
    if code != 1:
        logging.error("ERROR: Failed to authenticate with GitHub")
        return 1

    ### nodes
    logging.debug("Testing infrastructure nodes...")
    for host, user in (
            (config["nodes"]["monitor"], "admin"),
            (config["nodes"]["sync"]["host"], config["nodes"]["sync"]["user"]),
            (config["nodes"]["bridge"], "admin")):
        code = subprocess.call(["ssh", "-i", SSH_KEY, "%s@%s" %(user, host), "echo"],
            stdout=open(os.devnull), stderr=open(os.devnull))
        if code != 0:
            logging.error("ERROR: Failed to log into %s", host)
            return 1

    return 0
