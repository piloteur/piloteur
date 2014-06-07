from __future__ import absolute_import, print_function, division, unicode_literals

import os.path
import logging
import re
import tailer

from . import main

log = logging.getLogger('nexus.versions')

@main.API_call
def get_versions(hub_id=None):
    VERSIONS_PATH = os.path.join(main.config["data_path"], "logs",
                                 hub_id, "versions")
    try: listdir = main.sftp.listdir(VERSIONS_PATH)
    except IOError: return

    regex = re.compile(r'versions-log\.[\d\-]+\.csv')
    versions_files = sorted(os.path.join(VERSIONS_PATH, f)
                            for f in listdir
                            if regex.match(f))
    if not versions_files: return

    with main.sftp.open(versions_files[-1]) as f:
        line = tailer.tail(f, 1)
    if not line: return

    versions = line[0].split(',')

    return dict(zip((
        "timestamp",
        "ansible",
        "smart-home-config",
        "smarthome-deployment-blobs",
        "smarthome-drivers",
        "smarthome-hub-sync",
        "smarthome-reverse-tunneler",
    ), versions))

