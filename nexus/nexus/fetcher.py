from __future__ import absolute_import, print_function, division, unicode_literals

import os.path
import logging
import re
import tailer

from . import main

log = logging.getLogger('nexus.fetcher')

def get_data_files(hub_id, driver_name):
    DATA_PATH = os.path.join(main.config["data_path"], "data", hub_id)
    try: listdir = main.sftp.listdir(DATA_PATH)
    except IOError: return

    regex = re.compile(r'%s-[\d\-]+\.data' % re.escape(driver_name))
    data_files = sorted(os.path.join(DATA_PATH, f)
                        for f in listdir
                        if regex.match(f))

    return data_files

def get_logs_files(hub_id, driver_name):
    LOGS_PATH = os.path.join(main.config["data_path"], "logs", hub_id)
    LOGS_PATH = os.path.join(LOGS_PATH, driver_name + "-driver")
    try: listdir = main.sftp.listdir(LOGS_PATH)
    except IOError: return

    regex = re.compile(r'%s-[\d\-]+\.log' % re.escape(driver_name))
    log_files = sorted(os.path.join(LOGS_PATH, f)
                       for f in listdir
                       if regex.match(f))

    return log_files

def fetch_lines(files, n):
    lines = []
    for name in reversed(files):
        with main.sftp.open(name) as f:
            t = tailer.Tailer(f, read_size=30000)
            lines = t.tail(n - len(lines)) + lines
        if len(lines) == n: break

    return '\n'.join(lines)

def latest_timestamp(files):
    filename = files[-1]
    try: mtime = main.sftp.stat(filename).st_mtime
    except IOError: return

    return mtime

@main.API_call
def fetch_data(driver_name, n=100, hub_id=None):
    files = get_data_files(hub_id, driver_name)
    if not files: return

    return fetch_lines(files, n)

@main.API_call
def fetch_logs(driver_name, n=100, hub_id=None):
    files = get_logs_files(hub_id, driver_name)
    if not files: return

    return fetch_lines(files, n)

@main.API_call
def data_timestamp(driver_name, hub_id=None):
    files = get_data_files(hub_id, driver_name)
    if not files: return

    return latest_timestamp(files)

@main.API_call
def logs_timestamp(driver_name, hub_id=None):
    files = get_logs_files(hub_id, driver_name)
    if not files: return

    return latest_timestamp(files)


### Private API

def get_system_logs_files(hub_id, log_name):
    LOGS_PATH = os.path.join(main.config["data_path"], "logs", hub_id)
    LOGS_PATH = os.path.join(LOGS_PATH, log_name)
    try: listdir = main.sftp.listdir(LOGS_PATH)
    except IOError: return

    regex = re.compile(r'%s-log\.[\d\-]+\.\w+' % re.escape(log_name))
    log_files = sorted(os.path.join(LOGS_PATH, f)
                       for f in listdir
                       if regex.match(f))

    return log_files

@main.API_call
def fetch_system_logs(log_name, n=1, hub_id=None):
    files = get_system_logs_files(hub_id, log_name)
    if not files: return

    return fetch_lines(files, n)
