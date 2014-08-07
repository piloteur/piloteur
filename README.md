Put the check modules inside the `driver_checks` package, name one as a driver and it will be run for hubs that load that driver.

Remember that the module:

* needs to expose a `check(hub_id)` function
* can use the nexus library

See the nest_thermostat driver check as an example.
