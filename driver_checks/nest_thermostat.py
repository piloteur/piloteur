import arrow
import datetime
import time

from nexus import RED, YELLOW, GREEN, data_timestamp, get_timestamp, command_line

DRIVER_NAME = "nest_thermostat"
YELLOW_LIMIT = datetime.timedelta(seconds=30)
RED_LIMIT = datetime.timedelta(minutes=1)

def check(hub_id):
    sys_timestamp = arrow.get(get_timestamp())

    t = data_timestamp(DRIVER_NAME)
    if not t:
        last_write = arrow.get(0)
    else:
        last_write = arrow.get(t)

    health = GREEN
    if (sys_timestamp - last_write) > YELLOW_LIMIT:
        health = YELLOW
    if (sys_timestamp - last_write) > RED_LIMIT:
        health = RED

    message = ''
    if health != GREEN:
        message = 'last logged data {}'.format(last_write.humanize(sys_timestamp))

    return [{
        'name': 'driver/nest_thermostat',
        'status': health,
        'note': message,
        'timestamp': time.time()
    }]

if __name__ == '__main__':
    command_line()
