import time

from nexus import command_line, fetch_data, RED, GREEN

DRIVER_NAME = "tutorial"

# This is the standard tweakable check
# import datetime
# from .common import data_freshness_check
# RED_LIMIT = datetime.timedelta(minutes=1)
# check = data_freshness_check(DRIVER_NAME, RED_LIMIT)

def check(node_id):
    last_data_line = fetch_data(DRIVER_NAME, n=1)
    if last_data_line != "Im alive!":
        health = RED
    else:
        health = GREEN

    return [{
        'name': 'driver/tutorial',
        'status': health,
        'note': last_data_line,
        'timestamp': time.time()
    }]

if __name__ == '__main__':
    command_line()
