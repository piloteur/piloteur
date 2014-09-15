#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import json
import re

from .util import open_ssh, redirect_paramiko

def check(node_id, config, env):
    cmd = "python ~/piloteur-code/nodes/monitor/api/check.py"
    if node_id: cmd += " " + node_id
    client = open_ssh("bridge", config)
    stdin, stdout, stderr = client.exec_command(cmd)
    redirect_paramiko(None, stderr)
    # TODO: be more verbose

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
