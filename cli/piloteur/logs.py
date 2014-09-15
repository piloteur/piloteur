#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import nexus
import nexus.private

from .util import init_nexus

def logs(node_id, driver_name, log_type, num, config, env):
    init_nexus(config)

    if log_type == "logs":
        logs = nexus.fetch_logs(driver_name, n=int(num), node_id=node_id)
    elif log_type == "data":
        logs = nexus.fetch_data(driver_name, n=int(num), node_id=node_id)
    else:
        logging.error("The type can only be data or logs")
        return 1

    if not logs:
        logging.error("Logs or node not found")
        return 1

    print logs
    return 0

def syslog(node_id, log_name, num, config, env):
    init_nexus(config)

    logs = nexus.private.fetch_system_logs(log_name, n=int(num), node_id=node_id)

    if not logs:
        logging.error("Logs or node not found")
        return 1

    print logs
    return 0
