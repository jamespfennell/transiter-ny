"""
This Python 3.6+ script uses an official MTA resource and custom data in order to
generate the two direction name CSVs for the NYC subway.
"""
import csv

import requests

# This MTA CSV resource contains the basic direction names
STATIONS_CSV_URL = "http://web.mta.info/developers/data/nyct/subway/Stations.csv"

# In addition, some stops in the system can be broken up into two directions by using
# the track field that is provided in the MTA's GTFS Realtime feed. The following
# custom data defines these directions.

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

# The direction names will be outputted to these two files.
BASIC_CSV_FILE_PATH = "nyc_subway_direction_name_rules_basic.csv"
TRACK_CSV_FILE_PATH = "nyc_subway_direction_name_rules_with_track.csv"


def clean_mta_name(mta_name):
    if mta_name.strip() == "":
        return "(Terminating trains)"
    return mta_name.strip().replace("&", "and")


special_stop_id_to_basic_name = {}
with open(TRACK_CSV_FILE_PATH, "w") as f:
    csv_writer = csv.DictWriter(f, ["stop_id", "track", "direction_name"])
    csv_writer.writeheader()
    for row in csv.DictReader(SPECIAL_STOPS_CSV.strip().split("\n")):
        special_stop_id_to_basic_name[row["stop_id"]] = row["basic_name"]
        csv_writer.writerow(
            {
                "stop_id": row["stop_id"],
                "track": row["track"],
                "direction_name": row["track_name"],
            }
        )

with open(BASIC_CSV_FILE_PATH, "w") as f:
    csv_writer = csv.DictWriter(f, ["stop_id", "direction_name"])
    csv_writer.writeheader()

    stations_csv_data = requests.get(STATIONS_CSV_URL).text.split("\n")
    for row in csv.DictReader(stations_csv_data):
        stop_id_to_name = {
            row["GTFS Stop ID"] + "N": clean_mta_name(row["North Direction Label"]),
            row["GTFS Stop ID"] + "S": clean_mta_name(row["South Direction Label"]),
        }
        for stop_id, name in stop_id_to_name.items():
            name = special_stop_id_to_basic_name.get(stop_id, name)
            csv_writer.writerow({"stop_id": stop_id, "direction_name": name})

