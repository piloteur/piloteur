from __future__ import absolute_import, print_function, division, unicode_literals

import os.path
import logging

from . import main

log = logging.getLogger('nexus.utils')

@main.global_API_call
def list_hub_ids():
    LOGS_PATH = os.path.join(main.config["data_path"], "logs")
    return main.sftp.listdir(LOGS_PATH)
