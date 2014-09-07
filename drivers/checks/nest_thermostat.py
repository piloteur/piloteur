import datetime

from nexus import command_line
from .common import data_freshness_check

DRIVER_NAME = "nest_thermostat"
RED_LIMIT = datetime.timedelta(minutes=1)

check = data_freshness_check(DRIVER_NAME, RED_LIMIT)

if __name__ == '__main__':
    command_line()
