#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Piloteur command line management tool.

Usage:
  piloteur init
  piloteur [-v] --config=<config> test
  piloteur [-v] --config=<config> create_endpoint --node-id=<node-id> --node-classes=<classes> --on={rpi,ec2} [--at=<ip>] [--aws-type=<aws-type>]
  piloteur [-v] --config=<config> create_csv --on={rpi,ec2} <filename>
  piloteur [-v] --config=<config> create_node --type={monitor,sync,bridge,config} --on={arbitrary,ec2} [--at=<host>] [--aws-type=<aws-type>]
  piloteur [-v] --config=<config> connect <node-id>
  piloteur [-v] --config=<config> update <node-id>
  piloteur [-v] --config=<config> sync <node-id>
  piloteur [-v] --config=<config> decommission [--yes] <node-id>
  piloteur [-v] --config=<config> batch_decommission [--yes] <filename>
  piloteur [-v] --config=<config> logs [--type={data,logs}] [--num=<lines> | --hour=YYYY-MM-DD-HH] <node-id> <driver-name>
  piloteur [-v] --config=<config> syslog [--num=<lines> | --hour=YYYY-MM-DD-HH] <node-id> <log-name>
  piloteur [-v] --config=<config> config <node-id>
  piloteur [-v] --config=<config> check (--all | <node-id>)
  piloteur [-v] --config=<config> list [--include-offline] [<node-expression>]
  piloteur --config=<config> nexus_config
  piloteur (-h | --help)
  piloteur --version

Options:
  --config=<config>  Path to the cli-config.json.
  -v --verbose       Print debug output.
  -h --help          Show this screen.
  --version          Show version.

Command init: Interactively setup a network.

Command test: Check if the environment is set up properly.

Command create_endpoint: Create a new endpoint.
  --on=<strategy>            "ec2" (will create the instance) or "rpi"
  --at=<ip>                  IP address for the "rpi" strategy
  --aws-type=<aws-type>      Instance type for the "ec2" strategy [default: t2.micro]
  --node-id=<node-id>        Endpoint node-id
  --node-classes=<classes>   Endpoint node-classes, comma separated

Command create_csv: Create endpoints in bulk.
The csv format depends on the strategy: (no header, comma delimiter, " quote)
rpi - node_id,node_classes (space separated),IP_address
ec2 - node_id,node_classes (space separated),instance_type

Command create_node: Create a new infrastructure node.
#  --type={monitor,sync,bridge,config}      The node type to deploy.
#  --on=<strategy>            "ec2" (will create the instance) or "arbitrary"
#  --at=<ip>                  User and IP for the "arbitrary" strategy [ex: ubuntu@1.1.1.1]
#  --aws-type=<aws-type>      Instance type for the "ec2" strategy [default: t2.micro]

Command connect: Open a shell on an endpoint.

Command update: Run a Ansible update (soft redeploy) on the endpoint.

Command sync: Run a emergency rsync on the endpoint.

Command decommission: Disable and shut down the endpoint. IRREVERSIBLE.
  --yes     Don't ask for confirmation.

Command batch_decommission: Decommission all the endpoints listed in a file.
One node_id per line.

Command logs: Fetch driver logs or data.
  --type={data,logs}  What type of logs to fetch [default: logs]
  --num=<lines>       Number of (most recent) lines to tail [default: 50]
  --hour=<hour>       The hour of logs to retrieve in YYYY-MM-DD-HH format

Command syslog: Fetch system logs.

Command config: Print the endpoint config.

Command check: Run a verbose uncached check from the monitor.
  --all     Run on all the online endpoints

Command list: List the endpoints and their status from the monitor cache.
  --include-offline  List also offline endpoints
  <node-expression>  A partially matched regex to filter the nodes

Command nexus_config: Print the path of the nexus command line config
"""

from __future__ import absolute_import

import json
import os.path
import sys
import logging
from docopt import docopt

from .setup import setup, test
from .endpoint import connect, sync, update, decommission, batch_decommission
from .nexus import logs, syslog, get_config
from .monitor import check, list_endpoints
from .ansible import create_infra, create_endpoint, create_csv
from .init import init
from .util import CODE

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

    if arguments['create_endpoint']:
        if arguments['--on'] == 'ec2':
            if not arguments['--aws-type']:
                print >> sys.stderr, __doc__
                sys.exit(1)
        elif arguments['--on'] == 'rpi':
            if not arguments['--at'] or '@' in arguments['--at']:
                print >> sys.stderr, __doc__
                sys.exit(1)
        else:
            print >> sys.stderr, __doc__
            sys.exit(1)

        return create_endpoint(arguments['--on'], arguments['--at'],
            arguments['--node-id'], arguments['--node-classes'],
            arguments['--aws-type'], config, env)

    if arguments['create_csv']:
        return create_csv(arguments['--on'], arguments['<filename>'],
            config, env)

    if arguments['create_node']:
        if arguments['--on'] == 'ec2':
            if not arguments['--aws-type']:
                print >> sys.stderr, __doc__
                sys.exit(1)
        elif arguments['--on'] == 'arbitrary':
            if not arguments['--at'] or '@' not in arguments['--at']:
                print >> sys.stderr, __doc__
                sys.exit(1)
        else:
            print >> sys.stderr, __doc__
            sys.exit(1)

        return create_infra(arguments['--type'], arguments['--on'],
            arguments['--at'], arguments['--aws-type'], config, env)

    if arguments['connect']:
        return connect(arguments['<node-id>'], config, env)

    if arguments['update']:
        return update(arguments['<node-id>'], config, env)

    if arguments['sync']:
        return sync(arguments['<node-id>'], config, env)

    if arguments['decommission']:
        return decommission(arguments['<node-id>'], arguments['--yes'],
            config, env)

    if arguments['batch_decommission']:
        return batch_decommission(arguments['<node-id>'], arguments['--yes'],
            config, env)

    if arguments['logs']:
        return logs(arguments['<node-id>'], arguments['<driver-name>'],
            arguments['--type'], arguments['--num'], arguments['--hour'],
            config, env)

    if arguments['syslog']:
        return syslog(arguments['<node-id>'], arguments['<log-name>'],
            arguments['--num'], arguments['--hour'], config, env)

    if arguments['config']:
        return get_config(arguments['<node-id>'], config, env)

    if arguments['check']:
        return check(arguments['<node-id>'], config, env)

    if arguments['list']:
        return list_endpoints(arguments['<node-expression>'], arguments['--include-offline'], config, env)

    if arguments['nexus_config']:
        print os.path.join(CODE, "nexus", "config.json")
        return 0


if __name__ == '__main__':
    sys.exit(main())
