
# Smarthome monitoring

Checks are divided in 3 categories:

* Generic - these tests are performed by the monitor node to check the whole system health;
* Driver - these tests are implemented by driver authors using the Smarthome-NeXus library and are run by the monitor node for each node that has the corresponding driver enabled according to config;
* System - these tests are implemented and run on the node, logged to the remote location, and these logs are monitored by the monitor node.

The monitor node will detect running nodes by listing the nodes connected to the SSH tunnel. *(Are we fine with this?)*

## System tests format

System tests log to a timestamped synced log file, named `checks`, one entry per line.

System tests will advertise the checks running at start, every time a new logfile is created, and when checks change. This is the format:

```json
{'type': 'advert', 'checks': [
	{'name': 'xxx', 'period': 100},
	...
]}
```
	
The monitor will assume that a node not advertising, or not logging a check result for more than its period is failing.

The check result format is:

```json
{'type': 'result', 'name': 'xxx',
 'status': 'GREEN', 'note': '',
 'timestamp': 123456789}
```

## Code locations

*Generic* checks are implemented in the monitor node itself; *Driver* checks are implemented in smarthome-checks, in the `monitors` folder; *System* checks are implemented by the node itself.

# Smarthome-NeXus monitoring library

## Invocation and module layout

The monitor module should expose one single callable:

```python
check(hub_id)

-> [{'name': 'driver/test',
     'status': nexus.GREEN/YELLOW/RED,
     'note': str(), 'timestamp': int()}, ...]
```

*(Note: the return value might be later changed to a `nexus.Result` instance)*

And a global:

```python
PERIOD = 60
```

The monitor infrastructure will take care of calling `check()` every `PERIOD` seconds and registering the result.
	
For development, a helper is provided, that will turn the module into a command-line tool:

```python
if __name__ == '__main__':
	nexus.command_line()
```

The command line usage is as follows:

```
Usage: module.py [--config=<path>] <hub-id>

Options:
	--config=<path>  The path to Smarthome-NeXus JSON config
	                 [default: ~/.smarthome-nexus.json]
```

So here is a recommended skeleton of a monitor module:

```python
#! /usr/bin/env python

import nexus as nx
import time

__all__ = ['PERIOD', 'check']

PERIOD = 60

def check(hub_id):
	return [{
		'name': 'helloworld/xxx'
		'status': nx.GREEN,
		'note': '',
		'timestamp': time.time()
	}]
	
if __name__ == '__main__':
	smx.command_line()
```

Invoking it will work like this:

```
$ helloworld.py demo-hub
[2014-06-06 21:31:19,392] [INFO] nexus: The check() function would run every... 1 second(s)
[2014-06-06 21:31:19,392] [INFO] nexus: Running check('xxx')
[2014-06-06 19:31:19 -00:00] helloworld/xxx: GREEN ("")
```

## Configuration

The library needs to be configured to fetch the data for the tests. You don't need to worry about this when running inside the monitor infrastructure, but you'll need to this yourself to run the dev command-line tool.

A JSON configuration file looks like this:

```json
{
	"data_location": "admin@1.2.3.4:smarthome/",
	"ssh_key": "~/.smarthome-services", // optional
	"loglevel": "DEBUG"
}
```

*(Note: the monitor infrastructure will need more parameters)*

## API

In all calls, if `hub_id` is not specified it will default to the value `check()` was called with.

### fetch_data(driver_name, n=100, hub_id=None)

`fetch_data` will return the *n* most recent lines from data files with the passed *driver_name* (following the common naming convention).

Returns `None` if not found.

### fetch_logs(driver_name, n=100, hub_id=None)

`fetch_logs` will return the *n* most recent lines from log files with the passed *driver_name* (following the common naming convention).

Returns `None` if not found.

### data_timestamp(driver_name, hub_id=None)

`data_timestamp` will return the modified timestamp of the most recent data file with the passed *driver_name* (following the common naming convention).

Returns `None` if not found.

### logs_timestamp(driver_name, hub_id=None)

`logs_timestamp` will return the modified timestamp of the most recent log file with the passed *driver_name* (following the common naming convention).

Returns `None` if not found.
