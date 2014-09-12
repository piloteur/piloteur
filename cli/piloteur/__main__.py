#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Piloteur command line management tool.

Usage:
  piloteur [options] test
  piloteur [options] connect <node-id>
  piloteur (-h | --help)
  piloteur --version

Options:
  --config=<config>  Path to the config.
                     Defaults to config.yml in the "cli" folder.
  -v --verbose       Print debug output.
  -h --help          Show this screen.
  --version          Show version.
"""

from __future__ import absolute_import

import yaml
import os.path
import sys
import logging
from docopt import docopt

from .test import test
from .setup import setup
from .connect import connect
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


if __name__ == '__main__':
    sys.exit(main())
