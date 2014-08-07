from __future__ import absolute_import, print_function, division, unicode_literals

import os.path
import logging

from . import main
from .private import fetch_system_logs

log = logging.getLogger('nexus.utils')

@main.global_API_call
def list_hub_ids():
    LOGS_PATH = os.path.join(main.config["data_path"], "logs")
    return main.sftp.listdir(LOGS_PATH)

@main.API_call
def get_timestamp(hub_id=None):
    timesync_log = fetch_system_logs("timesync", hub_id=hub_id)
    if not timesync_log: return None
    return timesync_log.split(',')[0]
