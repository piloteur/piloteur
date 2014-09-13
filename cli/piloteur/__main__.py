#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Piloteur command line management tool.

Usage:
  piloteur [options] test
  piloteur [options] connect <node-id>
  piloteur [options] update <node-id>
  piloteur [options] sync <node-id>
  piloteur [options] logs [--type={data,logs}] [--num=<lines>] <node-id> <driver-name>
  piloteur [options] syslog [--num=<lines>] <node-id> <log-name>
  piloteur [options] config <node-id>
  piloteur [options] check (--all | <node-id>)
  piloteur [options] list [--all] [<node-expression>]
  piloteur [options] deploy-special [--type={monitor,sync,bridge}]
  piloteur (-h | --help)
  piloteur --version

Options:
  --config=<config>  Path to the config.
                     Defaults to config.yml in the "cli" folder.
  -v --verbose       Print debug output.
  -h --help          Show this screen.
  --version          Show version.

Command connect: Open a shell on a endpoint.

Command update: Run a code and config pull on the endpoint.

Command sync: Run a emergency rsync on the endpoint.

Command logs: Fetch driver logs or data.
  --type={data,logs}  What type of logs to fetch [default: logs]
  --num=<lines>       Number of lines to tail [default: 50]

Command syslog: Fetch system logs.
  --num=<lines>  Number of lines to tail [default: 50]

Command config: Print the endpoint config.

Command check: Run a verbose check from the monitor.
  --all  Run the check on all the connected endpoints

Command list: List the endpoints and their status from the monitor cache.
  --all              List also offline endpoints
  <node-expression>  A partially matched regex to filter the nodes

Command deploy-special: Deploy a infrastructure node.
Note: first create a box and add it to the config, run test and then this.
"""

from __future__ import absolute_import

import yaml
import os.path
import sys
import logging
from docopt import docopt

from .test import test
from .setup import setup
from .endpoint import connect, sync, update
from .logs import logs, syslog
from .monitor import check, get_config, list_endpoints
from .ansible import deploy_special
from .util import DIR

def main():
    arguments = docopt(__doc__, version='Piloteur CLI 1.0')

    config_path = arguments['--config'] or os.path.join(DIR, '..', 'config.yml')
    with open(config_path) as f:
        config = yaml.load(f)

    for k in config["paths"]:
        config["paths"][k] = os.path.expanduser(config["paths"][k])

    level = logging.INFO if arguments['--verbose'] else logging.WARN
    format = "[%(asctime)-15s] %(message)s"
    logging.basicConfig(format=format, level=level)

    setup(config)

    env = {
        'AWS_ACCESS_KEY_ID': config['AWS']['ACCESS_KEY'],
        'AWS_SECRET_ACCESS_KEY': config['AWS']['SECRET_KEY'],
    }

    if arguments['test']:
        return test(config, env)

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

    if arguments['deploy-special']:
        return deploy_special(arguments['--type'], config, env)


if __name__ == '__main__':
    sys.exit(main())
