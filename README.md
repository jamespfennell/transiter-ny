# NYC Subway integration for Transiter

This repository provides the configuration and code necessary to 
use [Transiter](https://github.com/jamespfennell/transiter) with the data feeds for the New York City Subway.

## Installation instructions

Assumptions:

1. You have a running Transiter instance.
1. You have an API key from the MTA. If not [you can get one here](https://datamine.mta.info/user/register).

First, in the same Python environment that Transiter is or will be running,
install the Python package contained in this repository:

    pip install transiter-nycsubway

Next, download all of the files in the config directory of this repository
to the computer from which you will be installing the transit system.
It may be easiest to just clone the repo. 

Navigate to the directory containing the config files.
The following curl
command makes the necessary HTTP request to install the system with ID `nycsubway`:

    curl -X PUT $TRANSITER_SERVER/systems/nycsubway \
        -F 'mta_api_key=$YOUR_MTA_API_KEY' \
        -F 'config_file=@nyc_subway_transiter_config.toml' \
        -F 'direction_name_rules_basic=@nyc_subway_direction_name_rules_basic.csv' \
        -F 'direction_name_rules_with_track=@nyc_subway_direction_name_rules_with_track.csv'
        
The install will take up to two minutes - most of this time is spent
inserting the half a million timetable entries into your database.

The configuration contains some sane defaults:

- The feeds are updated every 5 seconds.

- Four service maps are constructed using the subway's timetable: (1) daytime,
  (2) night-time, (3) weekend and (4) all times.
  
- A fifth service map is constructed using the realtime data.
  Given that an NYC subway routes' service map can change drastically
  due to planned work,
  this is really useful.

- For stops, the daytime and realtime service maps are shown.
  For routes, the all times and realtime service maps are shown.
  
Of course everything can be changed by playing with the TOML file.


## License note

The GTFS Realtime proto-buffers Python module is vendorized inside the package in
the
`gtfs-realtime.proto` and compiled `gtfs_realtime_pb2.py` files.
These are 
released under the Apache license.

New York City Transit's GTFS Realtime feed extension is also included inside
the package in the `nyct-subway.proto` and `nyct_subway_pb2.py` files. 
I'm currently having conversations with the MTA about the license of these.

All other code in this repository is original and
is released under the MIT license.

## Q&A for the curious

### Why does the NYC Subway have its own Python package?

The NYC Subway configuration here uses Transiter's built-in GTFS static parser,
provides a custom extension of Transiter's built-in GTFS realtime parser, 
and provides a custom extension to read the `ServiceStatusSubway.xml` feed. 

Having custom parsers for the NYC Subway, rather than relying purely on 
Transiter's built-in parsers, is necessary for a few reasons:

- The subway's realtime feeds use a GTFS Realtime extension to send extra
    data, such as which track each train will stop at. It's necessary
    to add extra logic to Transiter's GTFS Realtime parser in order to see
    this extra data.
    
- There are a couple of small bugs in the realtime feed which
    the parser fixes; for example, the J and Z trains are somewhat 'backwards'
    in Williamsburg and Bushwick.

- The alerts for the subway are not in the GTFS Realtime feeds; they're in an XML
    feed. Apparently it's some kind of standard 'SIRI' XML format,
    but because it's XML based there's no chance on earth I'll ever
    natively support it in Transiter.
     A custom parser for this XML feed is needed and contained here.

### Why do you vendorize the GTFS realtime proto-buffer module?

This is based on my understanding of how protocol buffer extensions work.
When you import a protobuf extension it alters
 the regular protobuf module to add the extra extension fields.
 In the context of Transiter this is a problem, because the 
 GTFS Realtime protobuf
 module is expected to be used to parse feeds other than those of the NYC Subway - 
 for example, if you install another transit system in your Transiter instance
 along with the NYC subway system.

With this approach the vendorized GTFS realtime 
probuf module is used to parse the NYC Subway, and 
the 'system' GTFS realtime
protobuf module used to parse feeds with Transiter's
built-in parser is left untouched.


