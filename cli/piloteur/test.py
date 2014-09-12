#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import subprocess
import os.path
import os

from .util import dep_call, open_ssh, CODE

def test(config, env):
    ### ec2.py
    logging.info("Testing ec2.py...")
    try:
        dep_call(["./ec2.py", "--list"], config, env)
    except subprocess.CalledProcessError:
        logging.error("ERROR: Error executing ec2.py, check your AWS credentials")
        return 1

    # TODO: test the keypair and the security group

    ### ssh keys
    logging.info("Testing SSH keys...")
    for name in ("piloteur-admin", "piloteur-devices",
                 "piloteur-admin.pub", "piloteur-devices.pub"):
        if not os.path.exists(os.path.join(CODE, "keys", name)):
            logging.error("The key %s is missing, place it in the keys/ folder", name)
            return 1
    try: open_ssh("github", config).close()
    except:
        logging.error("ERROR: Failed to authenticate with GitHub")
        return 1

    ### nodes
    logging.info("Testing infrastructure nodes...")
    for node_name in ("monitor", "sync", "bridge"):
        try: open_ssh(node_name, config).close()
        except:
            logging.error("ERROR: Failed to log into %s", node_name)
            return 1

    return 0
