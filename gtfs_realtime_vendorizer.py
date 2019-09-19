"""
Vendorize the GTFS realtime protobuf reader and add the NYCT extension on top of it

"""
import os
import requests
import subprocess

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
