import json
import paramiko
import os.path
import sys

from nexus import GREEN, YELLOW, init

PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT)
from monitor import get_bridge_connections, fetch_data, assess_data

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
        color = 'FAIL'
    elif res.node_health == GREEN:
        color = 'GREEN'
    elif res.node_health == YELLOW:
        color = 'YELLOW'
    else:
        color = 'RED'

    results.append({
        "node_health": color,
        "node_id": res.node_id,
        "summary": res.error or res.summary
    })

print json.dumps(results)
