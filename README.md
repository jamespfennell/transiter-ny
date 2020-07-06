# Transiter / New York

This repository contains configuration and code 
    for using [Transiter](https://github.com/jamespfennell/transiter) 
    with New York City area transit systems.
The Subway and PATH train are currently supported; additional
    systems (LIRR, MetroNorth) will be added in time.
    
    
## PATH Train

The PATH Train is simple to install:

    curl -X PUT $TRANSITER_SERVER/systems/us-ny-path \
        -F 'config_file=https://raw.githubusercontent.com/jamespfennell/transiter-nycsubway/master/nyc_subway_transiter_config.yaml'  


The Port Authority unfortunately does not distribute real time data directly.
The realtime data used by Transiter with this install comes
    indirectly and is missing many features:
    
- Only the next 4 trip stop events at a station are shown.

- There is no connection between the realtime trips and the scheduled trips.

More information can be found on the 
[PATH Train GTFS Realtime repository](https://github.com/jamespfennell/path-train-gtfs-realtime).

## New York City Subway

Pre-requisites:

1. You have an [API key from the MTA](https://api.mta.info).
1. The package `transiter_ny_mta` is installed in your Transiter instance.
   - If you're running Transiter using containers, it must be 
        installed in all containers (using `docker exec <container_id> pip install transiter_ny_mta`).
   - If you're running Transiter through a Python virtual env, just
        install the package in the env (`pip install transiter_ny_mta`).

To install the subway with system ID `us-ny-subway`, execute the following HTTP request:

    curl -X PUT $TRANSITER_SERVER/systems/us-ny-subway \
        -F 'mta_api_key=$YOUR_MTA_API_KEY' \
        -F 'config_file=https://raw.githubusercontent.com/jamespfennell/transiter-nycsubway/master/nyc_subway_transiter_config.yaml'
        
The install will take up to 75 seconds - most of this time is spent
inserting the half a million timetable entries into the database.

The system's YAML configuration contains some sane defaults:

- The 10 realtime feeds are updated every 5 seconds.

- Four service maps are constructed using the subway's timetable: (1) daytime,
  (2) night-time, (3) weekend and (4) all times.
  A fifth service map is constructed using the realtime data.

Of course everything can be changed by playing with the YAML config file.


## License note

The protobuf definitions and Python builds for both
    GTFS Realtime
    and the MTA extensions are vendorized in this repository
    and released under the Apache license.

All other code in this repository is original and
is released under the MIT license.




