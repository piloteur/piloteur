import sys
import json

from nest_thermostat import NestThermostat

def main():
    config = json.load(sys.stdin)
    devices = config.get('driver_config', {}).get('nest_thermostat', {}).get('devices')
    interval = config.get('driver_config', {}).get('nest_thermostat', {}).get('interval')
    if devices is None or not interval:
        print >> sys.stderr, 'ERROR: missing config parameters'
        sys.exit(1)

    n = NestThermostat(devices, interval)
    n.run()

if __name__ == '__main__':
    main()
