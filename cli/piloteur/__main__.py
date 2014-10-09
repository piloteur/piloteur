#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Piloteur command line management tool.

Usage:
  piloteur init
  piloteur [-v] --config=<config> test
  piloteur [-v] --config=<config> create --endpoint --node-id=<node-id> --node-classes=<classes> (--on=rpi --at=<host> | --on=ec2 [--aws-type=<aws-type>])
  piloteur [-v] --config=<config> create --type={monitor,sync,bridge,config} (--on=arbitrary --at=<host> | --on=ec2 [--aws-type=<aws-type>])
  piloteur [-v] --config=<config> connect <node-id>
  piloteur [-v] --config=<config> update <node-id>
  piloteur [-v] --config=<config> sync <node-id>
  piloteur [-v] --config=<config> logs [--type={data,logs}] [--num=<lines>] <node-id> <driver-name>
  piloteur [-v] --config=<config> syslog [--num=<lines>] <node-id> <log-name>
  piloteur [-v] --config=<config> config <node-id>
  piloteur [-v] --config=<config> check (--all | <node-id>)
  piloteur [-v] --config=<config> list [--all] [<node-expression>]
  piloteur (-h | --help)
  piloteur --version

Options:
  --config=<config>  Path to the cli-config.json.
  -v --verbose       Print debug output.
  -h --help          Show this screen.
  --version          Show version.

Command init: Interactively setup a network.

Command test: Check if the environment is set up properly.

Command create: Create a new node.
  --on=<strategy>   ec2 (will create the instance), rpi or arbitrary
  --at=<ip>         If not deploying to EC2, this is the target box
                    For non-endpoints, specify the user too: user@host
  --node-id=<node-id>        Endpoint node-id
  --node-classes=<classes>   Endpoint node-classes, comma separated
  --aws-type=<aws-type>      EC2 instance type [default: t2.micro]

Command connect: Open a shell on a endpoint.

Command update: Run a code and config pull on the endpoint.

Command sync: Run a emergency rsync on the endpoint.

Command logs: Fetch driver logs or data.
  --type={data,logs}  What type of logs to fetch [default: logs]
  --num=<lines>       Number of lines to tail [default: 50]

Command syslog: Fetch system logs.

Command config: Print the endpoint config.

Command check: Run a verbose check from the monitor.

Command list: List the endpoints and their status from the monitor cache.
  --all              List also offline endpoints
  <node-expression>  A partially matched regex to filter the nodes
"""

from __future__ import absolute_import

import json
import os.path
import sys
import logging
from docopt import docopt

from .setup import setup, test
from .endpoint import connect, sync, update
from .nexus import logs, syslog, get_config
from .monitor import check, list_endpoints
from .ansible import create_infra, create_endpoint
from .init import init
# from .util import DIR

def main():
    arguments = docopt(__doc__, version='Piloteur CLI 1.0')

    level = logging.INFO if arguments['--verbose'] else logging.WARN
    format = "[%(asctime)-15s] %(message)s"
    logging.basicConfig(format=format, level=level)

    if arguments['init']:
        return init()

    if not arguments['--config']:
        print "Please specify a --config"
        return 1

    config_path = arguments['--config'] # or os.path.join(DIR, '..', 'config.json')
    with open(config_path) as f:
        config = json.load(f)

    for k in config["paths"]:
        if type(config["paths"][k]) == dict:
            for x in config["paths"][k]:
                config["paths"][k][x] = os.path.expanduser(config["paths"][k][x])
        else:
            config["paths"][k] = os.path.expanduser(config["paths"][k])

    setup(config)

    env = {
        'AWS_ACCESS_KEY_ID': config['AWS']['ACCESS_KEY'],
        'AWS_SECRET_ACCESS_KEY': config['AWS']['SECRET_KEY'],
    }

    if arguments['test']:
        return test(config, env)

    if arguments['create']:
        if arguments['--endpoint']:
            return create_endpoint(arguments['--on'], arguments['--at'],
                arguments['--node-id'], arguments['--node-classes'],
                arguments['--aws-type'], config, env)
        return create_infra(arguments['--type'], arguments['--on'],
            arguments['--at'], arguments['--aws-type'],
            config, env)

    if arguments['connect']:
        return connect(arguments['<node-id>'], config, env)

    if arguments['update']:
        return update(arguments['<node-id>'], config, env)

    if arguments['sync']:
        return sync(arguments['<node-id>'], config, env)

    if arguments['logs']:
        return logs(arguments['<node-id>'], arguments['<driver-name>'],
            arguments['--type'], arguments['--num'], config, env)

    if arguments['syslog']:
        return syslog(arguments['<node-id>'], arguments['<log-name>'],
            arguments['--num'], config, env)

    if arguments['config']:
        return get_config(arguments['<node-id>'], config, env)

    if arguments['check']:
        return check(arguments['<node-id>'], config, env)

    if arguments['list']:
        return list_endpoints(arguments['<node-expression>'], arguments['--all'], config, env)


if __name__ == '__main__':
    sys.exit(main())
