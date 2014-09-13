import os.path
import sqlite3
import json
import paramiko
import nexus
import sys

PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT)
from monitor import get_bridge_connections

with open(os.path.expanduser('~/piloteur-config/monitor/config.json')) as f:
    config = json.load(f)

for _ in range(5):
    try:
        nexus.init(config)
    except paramiko.SSHException:
        continue
    break
else:
    exit(1)

online_nodes = get_bridge_connections(config['bridge_host'])

DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(DIR, '..', 'cache.db')

c = sqlite3.connect(db_path).cursor()

nodes = []
c.execute('SELECT * FROM Cache')
for node_id, node_health, summary, cache_time in c.fetchall():
    nodes.append({
        "node_id": node_id,
        "node_health": node_health,
        "summary": summary,
        "cache_time": cache_time,
        "online": node_id in online_nodes,
    })

