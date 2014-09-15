#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging

from .util import call_ansible

def deploy_special(node_type, config, env):
    if node_type not in ("sync", "monitor", "bridge", "config"):
        logging.error("Unknown type")
        return 1

    call_ansible([
        "-i", "inventory.ini",
        "-l", "%s-nodes" % node_type,
        "%s_node.yml" % node_type
    ], config, env)
