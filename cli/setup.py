#!/usr/bin/env python2
#-*- coding:utf-8 -*-

from distutils.core import setup

setup(
    name='piloteur-cli',
    version='1.0',
    packages=['piloteur'],
    entry_points = {
        'console_scripts': [
            'piloteur = piloteur.__main__:main',
        ]
    }
)
