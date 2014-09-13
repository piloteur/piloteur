import json
import paramiko
import os.path
import sys

from nexus import GREEN, init
from monitor import get_bridge_connections, fetch_data, assess_data

DIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.expanduser('~/piloteur-config/monitor/config.json')) as f:
    config = json.load(f)

for _ in range(5):
    try:
        init(config)
    except paramiko.SSHException:
        continue
    break
else:
    exit(1)

if len(sys.argv) == 1:
    nodes_list = get_bridge_connections(config['bridge_host'])
else:
    nodes_list = [sys.argv[1]]

results = []
for node_id in nodes_list:
    data = fetch_data(node_id, config)
    res = assess_data(data, config)

    if res.error:
        color = 'RED'
    elif res.node_health != GREEN:
        color = 'YELLOW'
    else:
        color = 'GREEN'

    results.append({
        "color": color,
        "node_id": res.node_id,
        "result": res.error or res.summary
    })

print json.dumps(results)
