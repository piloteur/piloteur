import json
import paramiko
import os.path

from nexus import GREEN, init
from nexus.monitor import get_tunnel_connections, fetch_data, assess_data

DIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(DIR, 'config.json')) as f:
    config = json.load(f)

for _ in range(5):
    try:
        init(config)
    except paramiko.SSHException:
        continue
    break
else:
    exit(1)

hubs_list = get_tunnel_connections(config['tunnel_info'])

results = []
for hub_id in hubs_list:
    data = fetch_data(hub_id)
    res = assess_data(data)

    if res.error:
        color = 'RED'
    elif res.hub_health != GREEN:
        color = 'YELLOW'
    else:
        color = 'GREEN'

    print('[{}] {}... {}'.format(color, res.hub_id, res.error or res.summary))
