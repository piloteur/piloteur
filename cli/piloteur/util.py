#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import subprocess
import os
import os.path

DIR = os.path.dirname(os.path.realpath(__file__))
CODE = os.path.join(DIR, '..', '..')
DEPLOYMENT = os.path.join(CODE, 'deployment')

def dep_call(command, config, env):
    cmd_env = os.environ.copy()
    cmd_env.update(env)
    cmd_env["PATH"] = (os.path.join(config["paths"]["virtualenv"], "bin")
        + ":" + cmd_env["PATH"])
    return subprocess.check_output(command, env=cmd_env, cwd=DEPLOYMENT)
