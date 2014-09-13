#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import json
import nexus
import nexus.private

from .util import open_ssh, init_nexus

def check(node_id, config, env):
    cmd = "~/piloteur-code/nodes/monitor/api/check.py"
    if node_id: cmd += " " + node_id
    client = open_ssh("bridge", config)
    stdin, stdout, stderr = client.exec_command(cmd)
    # TODO: connect stderr and be more verbose

    res = json.load(stdout)
    for r in res:
        print '[{node_id}] {color}... {result}'.format(**r)

    client.close()
    return 0

def get_config(node_id, config, env):
    init_nexus(config)

    if node_id not in nexus.list_node_ids():
        logging.error("Node ID not found.")
        return 1

    classes_log = nexus.private.fetch_system_logs("classes")
    if not classes_log:
        logging.error("Missing classes data.")
        return 1
    remote_node_id = classes_log.split(',')[0]
    if not remote_node_id == node_id:
        logging.error("Mismatching node_id?!")
        return 1
    classes = classes_log.split(',')[1:].join(' ')

    # TODO: run locally
    config_cmd = "~/piloteur-code/nodes/endpoint/config.py %s %s" % (node_id, classes)

    client = open_ssh("monitor", config)
    stdin, stdout, stderr = client.exec_command(config_cmd)

    node_config = json.loads(stdout.read())
    print json.dumps(node_config, indent=4)

    client.close()

    return 0
