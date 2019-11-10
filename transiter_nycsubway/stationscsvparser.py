"""
This Python 3.6+ script uses an official MTA resource and custom data in order to
generate the two direction name CSVs for the NYC subway.
"""
import csv

from transiter import models

# Some stops in the system can be broken up into two directions by using
# the track field that is provided in the MTA's GTFS Realtime feed. The following
# custom data defines these directions. Other directions come automatically from
# the feed content.

EAST_SIDE_AND_QUEENS = "East Side and Queens"
MANHATTAN = "Manhattan"
ROCKAWAYS = "Euclid - Lefferts - Rockaways"  # To be consistent with the MTA
UPTOWN = "Uptown"
UPTOWN_AND_THE_BRONX = "Uptown and The Bronx"
QUEENS = "Queens"

SPECIAL_STOPS_CSV = f"""
stop_id,track,track_name,basic_name
A42N,E2,"Court Sq, Queens",{MANHATTAN}
A42S,E1,"Church Av, Brooklyn",{ROCKAWAYS}
A41S,B1,Coney Island,{ROCKAWAYS}
A25N,D4,{EAST_SIDE_AND_QUEENS},{UPTOWN_AND_THE_BRONX}
D15N,B2,{EAST_SIDE_AND_QUEENS},{UPTOWN_AND_THE_BRONX}
R14N,A4,{UPTOWN},{QUEENS}
B08N,T2,{QUEENS},{UPTOWN}
D14N,D4,{EAST_SIDE_AND_QUEENS},{UPTOWN_AND_THE_BRONX}
D26N,A2,Franklin Avenue,{MANHATTAN}
"""


# Additional arguments are accepted for forwards compatibility
# noinspection PyUnusedLocal
def parse(binary_content, *args, **kwargs):
    priority = 0
    special_stop_id_to_basic_name = {}

    csv_reader = csv.DictReader(SPECIAL_STOPS_CSV.strip().splitlines())
    for row in csv_reader:
        special_stop_id_to_basic_name[row["stop_id"]] = row["basic_name"]
        yield models.DirectionRule(
            id=str(priority),
            priority=priority,
            stop_id=row["stop_id"],
            name=row["track_name"],
            track=row["track"],
        )
        priority += 1

    csv_reader = csv.DictReader(binary_content.decode("utf-8").splitlines())
    for row in csv_reader:
        stop_id_to_name = {
            row["GTFS Stop ID"] + "N": clean_mta_name(row["North Direction Label"]),
            row["GTFS Stop ID"] + "S": clean_mta_name(row["South Direction Label"]),
        }
        for stop_id, name in stop_id_to_name.items():
            name = special_stop_id_to_basic_name.get(stop_id, name)
            yield models.DirectionRule(
                id=str(priority),
                priority=priority,
                stop_id=stop_id,
                name=name,
                track=None,
            )
            priority += 1


def clean_mta_name(mta_name):
    if mta_name.strip() == "":
        return "(Terminating trains)"
    return mta_name.strip().replace("&", "and")
