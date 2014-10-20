#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import logging
import json
import sys
import os.path
import nexus
import nexus.private

from .util import init_nexus, CONFIG_NODE

sys.path.append(CONFIG_NODE)
import config as c

def logs(node_id, driver_name, log_type, num, hour, config, env):
    init_nexus(config)

    if log_type == "logs":
        fetcher = nexus.fetch_logs
    elif log_type == "data":
        fetcher = nexus.fetch_data
    else:
        logging.error("The type can only be data or logs")
        return 1

    if hour:
        logs = fetcher(driver_name, h=hour, node_id=node_id)
    else:
        logs = fetcher(driver_name, n=int(num), node_id=node_id)

    if not logs:
        logging.error("Logs or node not found")
        return 1

    print logs
    return 0

def syslog(node_id, log_name, num, hour, config, env):
    init_nexus(config)

    if hour:
        logs = nexus.private.fetch_system_logs(log_name, h=hour, node_id=node_id)
    else:
        logs = nexus.private.fetch_system_logs(log_name, n=int(num), node_id=node_id)

    if not logs:
        logging.error("Logs or node not found")
        return 1

    print logs
    return 0

def get_config(node_id, config, env):
    init_nexus(config)

    logging.info("Fetching the nodes list...")
    if node_id not in nexus.list_node_ids():
        logging.error("Node ID not found.")
        return 1

    logging.info("Node found, fetching the classes info...")
    classes_log = nexus.private.fetch_system_logs("classes", node_id=node_id)
    if not classes_log:
        logging.error("Missing classes data.")
        return 1
    remote_node_id = classes_log.split(',')[0]
    if not remote_node_id == node_id:
        logging.error("Mismatching node_id?!")
        return 1
    classes = classes_log.split(',')[1:]

    logging.info("Generating config...")
    CONFIG_DIR = os.path.join(config['paths']['config_repo'], 'endpoint')
    node_config = c.make_config(node_id, classes, config_dir=CONFIG_DIR)
    print json.dumps(node_config, indent=4)

    return 0
