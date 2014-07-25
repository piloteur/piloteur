#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os.path
import json
import time

import nexus
import nexus.private
import nexus.monitor


class Alerting():
    def __init__(self, config):
        self.config = config

    def run(self):
        while True:
            time.sleep(1)


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, '..', 'config.json')) as f:
        config = json.load(f)

    A = Alerting(config)
    A.run()
