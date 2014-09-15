import datetime
import json
import sys
import os.path

"""
Usage: output-redirector {-d|-l} name
"""

with open(os.path.expanduser('~/config.json')) as f:
    config = json.load(f)

driver_name = sys.argv[2]

DATA_PATH = os.path.expanduser(config['data_path'])
LOGS_PATH = os.path.expanduser(config['logs_path'])

if sys.argv[1] == '-d':
    filename = os.path.join(DATA_PATH, '%(name)s-%(hour)s.data')
    prefix = ''
elif sys.argv[1] == '-l':
    filename = os.path.join(LOGS_PATH, '%(name)s-driver',
        '%(name)s-%(hour)s.log')
    prefix = '[%(timestamp)s] '
else:
    sys.exit(1)

hour, f = None, None
while True:
    try: line = raw_input()
    except EOFError: break
    hour_now = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H')
    if hour_now != hour:
        hour = hour_now
        if f: f.close()
        f = open(filename % {'name': driver_name, 'hour': hour}, 'a')
    timestamp = datetime.datetime.utcnow().isoformat()
    f.write(prefix % {'timestamp': timestamp} + line + '\n')
    f.flush()

if f: f.close()
