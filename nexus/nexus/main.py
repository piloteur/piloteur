from __future__ import absolute_import, print_function, division, unicode_literals

import sys
import docopt
import os.path
import json
import logging
import arrow
import paramiko
import functools

### Globals

config = None
node_id = None
log = logging.getLogger('nexus')
client = None
sftp = None

### Constants

GREEN = 0
YELLOW = 1
RED = 2

### Helpers

def args_namer(func, args, kwargs):
    code = func.func_code
    names = code.co_varnames[:code.co_argcount]
    all_args = kwargs.copy()
    for n, v in zip(names, args):
        all_args[n] = v
    return all_args

def API_call(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if config is None or sftp is None:
            raise RuntimeError("Library not initialized with init()")
        all_args = args_namer(f, args, kwargs)
        if not all_args.get('node_id'):
            if node_id is None:
                raise RuntimeError("No node_id passed and no check() context")
            all_args['node_id'] = node_id
        return f(**all_args)
    return wrapper

def global_API_call(f):
    # TODO: merge with the above API_call
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if config is None or sftp is None:
            raise RuntimeError("Library not initialized with init()")
        return f(*args, **kwargs)
    return wrapper

### API functions

def set_node_id(new_node_id):
    global node_id
    node_id = new_node_id

def init(new_config):
    global config
    config = new_config

    level = getattr(logging, config.get("loglevel", "INFO"), logging.INFO)
    format = "[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(format=format, level=level)

    if level > logging.DEBUG:
        logging.getLogger('paramiko').setLevel(logging.WARNING)

    if not "data_location" in config or not ':' in config["data_location"] \
                                     or not '@' in config["data_location"]:
        log.error("Mandatory config option data_location not present or malformed.")
        sys.exit(1)

    data_location, path = config["data_location"].rsplit(':', 1)
    config["data_path"] = path

    port = 22
    if ':' in data_location:
        data_location, port = data_location.split(':')
        port = int(port)
    username, hostname = data_location.split('@')
    key_filename = config.get("ssh_key", None)
    if key_filename:
        key_filename = os.path.expanduser(key_filename)

    log.debug("hostname:%s port:%d username:%s path:%s key_filename:%s",
        hostname, port, username, path, key_filename)

    global client
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, key_filename=key_filename)

    global sftp
    sftp = client.open_sftp()

    log.debug("</init>")

def command_line():
    DOC = """
Usage: %s [--config=<path>] <node-id>

Options:
    --config=<path> The path to the nexus JSON config
                    [default: ~/.piloteur.json]
    """ % sys.argv[0]

    arguments = docopt.docopt(DOC)

    path = os.path.expanduser(arguments['--config'])
    if not os.path.isfile(path):
        log.error("Config file not existing.")
        sys.exit(1)
    with open(path) as f:
        config = json.load(f)

    init(config)

    if not hasattr(sys.modules['__main__'], 'PERIOD') or not hasattr(sys.modules['__main__'], 'check'):
        log.error("PERIOD global or check function not found.")
        sys.exit(1)

    log.info("The check() function would run every... %d second(s)", sys.modules['__main__'].PERIOD)

    global node_id
    node_id = arguments["<node-id>"]

    log.info("Running check('%s')", node_id)
    results = sys.modules['__main__'].check(node_id)

    for r in results:
        t = arrow.get(r["timestamp"]).format('YYYY-MM-DD HH:mm:ss ZZ')
        s = ('GREEN' if r["status"] == GREEN
             else 'YELLOW' if r["status"] == YELLOW
             else 'RED')
        print('[%s] %s: %s ("%s")' % (t, r["name"], s, r["note"]))
