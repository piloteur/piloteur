#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import json
import nexus
import nexus.private
import re

from .util import open_ssh, init_nexus

def check(node_id, config, env):
    cmd = "python ~/piloteur-code/nodes/monitor/api/check.py"
    if node_id: cmd += " " + node_id
    client = open_ssh("bridge", config)
    stdin, stdout, stderr = client.exec_command(cmd)
    # TODO: connect stderr and be more verbose

    retcode = 0
    res = json.load(stdout)
    for r in res:
        if r["node_health"] != "GREEN": retcode = 1
        print '[{node_id}] {node_health}... {summary}'.format(**r)

    client.close()
    return retcode

def list_endpoints(regex, also_offline, config, env):
    cmd = "python ~/piloteur-code/nodes/monitor/api/cache.py"
    client = open_ssh("bridge", config)
    stdin, stdout, stderr = client.exec_command(cmd)

    res = json.load(stdout)
    for r in res:
        if not also_offline and not r["online"]: continue
        if regex and not re.search(regex, r["node_id"]): continue
        print '[{cache_time}] [{node_id}] (online: {online}) {node_health}... {summary}'.format(**r)

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
    config_cmd = "python ~/piloteur-code/nodes/endpoint/config.py %s %s" % (node_id, classes)

    client = open_ssh("monitor", config)
    stdin, stdout, stderr = client.exec_command(config_cmd)

    node_config = json.loads(stdout.read())
    print json.dumps(node_config, indent=4)

    client.close()

    return 0
