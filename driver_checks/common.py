import arrow
import time

from nexus import RED, YELLOW, GREEN, data_timestamp, get_timestamp

def data_freshness_check(driver_name, red_limit, yellow_limit=None):
    if yellow_limit is None:
        yellow_limit = red_limit / 2

    def check(hub_id):
        sys_timestamp = arrow.get(get_timestamp())

        t = data_timestamp(driver_name)
        if not t:
            last_write = arrow.get(0)
        else:
            last_write = arrow.get(t)

        health = GREEN
        if (sys_timestamp - last_write) > yellow_limit:
            health = YELLOW
        if (sys_timestamp - last_write) > red_limit:
            health = RED

        message = ''
        if health != GREEN:
            message = 'last logged data {}'.format(last_write.humanize(sys_timestamp))

        return [{
            'name': 'driver/data_freshness/{}'.format(driver_name),
            'status': health,
            'note': message,
            'timestamp': time.time()
        }]

    return check
