"""
Vendorize the GTFS realtime protobuf reader and add the NYCT extension on top of it.

The reader is vendorized because the NYCT extension works by modifying the GTFS realtime
reader. By default, it modifies the standard reader google.transiter.gtfs_realtime_pb2.
Given the structure of the reader this is _probably_ okay, but it's safest to vendorize
it because, in Transiter, the standard reader is used by other parsers.

The main difficulty in vendorizing the readers is that the protobuf system namespaces
code in a similar way to the namespacing of Java code. Given a package and a
definition inside that package, the protobuf system assumes (package, definition) is
_globally_ unique. Because of this, we can't do the usual easy Python vendorization
where we just duplicate the gtfs_realtime_pb2.py file and import it separately.

In addition, the profobuf system appears to have two different ways of determining the
package of a protobuf file. The C++ protobuf compiler uses the package declaration
in the proto file. The native Python protobuf compiler uses the location of the proto
file on disk relative to the current working directory. This vendorization script covers
both cases - i.e., ensures that whichever way the package is determined it does not
collide with the package of google.transit.gtfs_realtime_pb2. From trial and error,
covering both cases seems to be necessary.
"""

import os
import requests
import subprocess
import dataclasses

GTFS_RT_PROTO_URL = (
"https://raw.githubusercontent.com/google/transit"
"/master/gtfs-realtime/proto/gtfs-realtime.proto"
)
TRANSITER_EXT_PROTO_URL = ""


@dataclasses.dataclass
class Config:
    key: str
    mta_ext_proto_url: str


alerts_config = Config(
    key="alerts",
    mta_ext_proto_url=(
        "https://raw.githubusercontent.com/OneBusAway/onebusaway-gtfs-realtime-api"
        "/master/src/main/resources/com/google/transit/realtime/"
        "gtfs-realtime-service-status.proto"
    )
)




OUTPUT_DIR = "transiter_nycsubway/gtfs"
GTFS_REALTIME_PROTO_URL = "https://raw.githubusercontent.com/google/transit/master/gtfs-realtime/proto/gtfs-realtime.proto"
NYC_TRANSIT_PROTO_URL = (
    "http://datamine.mta.info/sites/all/files/pdfs/nyct-subway.proto.txt"
)


os.makedirs(OUTPUT_DIR, exist_ok=True)

gtfs_realtime_proto_raw = requests.get(GTFS_REALTIME_PROTO_URL).text

gtfs_realtime_proto = gtfs_realtime_proto_raw.replace(
    'optional java_package = "com.google.transiter.realtime";',
    'optional java_package = "com.transiter.nycsubway";',
    1,
).replace("package transit_realtime;", "package transiter_nycsubway;", 1)

gtfs_realtime_proto_location = os.path.join(OUTPUT_DIR, "gtfs-realtime.proto")
with open(gtfs_realtime_proto_location, "w") as f:
    f.write(gtfs_realtime_proto)


nyc_transit_proto_raw = requests.get(NYC_TRANSIT_PROTO_URL).text

nyc_transit_proto = "\n".join(
    [
        'syntax = "proto2";',
        "package transiter_nycsubway;",
        nyc_transit_proto_raw.replace(
            'optional java_package = "com.google.transiter.realtime";',
            'optional java_package = "com.transiter.nycsubway";',
            1,
        )
        .replace(
            'import "gtfs-realtime.proto";',
            'import "{}";'.format(gtfs_realtime_proto_location),
            1,
        )
        .replace("transit_realtime", "transiter_nycsubway"),
    ]
)

nyc_transit_proto_location = os.path.join(OUTPUT_DIR, "nyct-subway.proto")
with open(nyc_transit_proto_location, "w") as f:
    f.write(nyc_transit_proto)

subprocess.run(["protoc", "--python_out", ".", gtfs_realtime_proto_location])
subprocess.run(["protoc", "--python_out", ".", nyc_transit_proto_location])


# Test that we can safely import both the standard reader and the vendorized reader
from google.transit import gtfs_realtime_pb2
from transiter_nycsubway.gtfs import gtfs_realtime_pb2 as gtfs_realtime_pb2_vendorized
from transiter_nycsubway.gtfs import nyct_subway_pb2

packages = [gtfs_realtime_pb2, gtfs_realtime_pb2_vendorized, nyct_subway_pb2]
