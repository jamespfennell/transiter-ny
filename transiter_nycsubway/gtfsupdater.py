#
# (c) James Fennell 2019. Released under the MIT License.
#
"""
Module that provides the parser for the NYC Subway's GTFS Realtime feeds.
"""
from transiter.services.update import tripupdater, gtfsrealtimeutil

from transiter_nycsubway import gtfs_realtime_pb2, nyct_subway_pb2


def merge_in_nyc_subway_extension_data(data):
    data["header"].pop("nyct_feed_header", None)

    for entity in data["entity"]:
        stop_time_updates = []
        trip = None
        if "trip_update" in entity:
            main_entity = entity["trip_update"]
            # trip = entity['trip_update']['trip']
            stop_time_updates = entity["trip_update"].get("stop_time_update", [])
        elif "vehicle" in entity:
            main_entity = entity["vehicle"]
            # trip = entity['vehicle']['trip']
        else:
            continue
        trip = main_entity["trip"]

        nyct_trip_data = trip.get("nyct_trip_descriptor", {})

        train_id = nyct_trip_data.get("train_id", None)
        if train_id is not None:
            main_entity["vehicle"] = {"id": train_id}

        direction = nyct_trip_data.get("direction", None)
        # NOTE: it seems the NYCT direction is NORTH if it's missing.
        # TODO: May be more robust to infer it from the trip ID.
        if direction is None:
            direction = "NORTH"
        if direction is not None:
            trip["direction_id"] = direction == "SOUTH"

        if "vehicle" in entity:
            if nyct_trip_data.get("is_assigned", False):
                entity["current_status"] = "SCHEDULED"

        del trip["nyct_trip_descriptor"]

        for stop_time_update in stop_time_updates:
            nyct_stop_event_data = stop_time_update.get("nyct_stop_time_update", None)
            if nyct_stop_event_data is None:
                continue

            stop_time_update["track"] = nyct_stop_event_data.get(
                "actual_track", nyct_stop_event_data.get("scheduled_track", None)
            )
            del stop_time_update["nyct_stop_time_update"]

    return data


# TODO: probably this is not needed
def duplicate_stops_problem(__, trip):

    stop_ids = set()
    for stop_time in trip.stop_times:
        if stop_time.stop_id in stop_ids:
            return False

    return True


def fix_route_ids(__, trip):
    if trip.route_id == "5X":
        trip.route_id = "5"
    if trip.route_id == "" or trip.route_id == "SS":
        return False
    return True


def delete_old_scheduled_trips(feed_update, trip):
    reference_time = feed_update.feed_time
    if trip.current_status != "SCHEDULED":
        return True
    if (reference_time - trip.start_time).total_seconds() > 300:
        return False
    return True


def fix_current_stop_sequence(__, trip):
    current_stop_id = trip.current_stop_id
    if current_stop_id is None or len(current_stop_id) > 3:
        return True
    offset = None
    for stop_time in trip.stop_times:
        if stop_time.stop_id[0:3] == current_stop_id:
            trip.current_stop_id = stop_time.stop_id
            offset = trip.current_stop_sequence - stop_time.stop_sequence
            break
    if offset is None:
        # TODO: we should possibly return False here as this is a buggy trip
        return True
    for stop_time in trip.stop_times:
        stop_time.stop_sequence += offset
    return True


def invert_j_train_direction_in_bushwick(__, stop_time_update):
    route_id = stop_time_update.trip.route_id
    if route_id != "J" and route_id != "Z":
        return True
    stop_id = stop_time_update.stop_id
    if stop_id[:3] not in {"M11", "M12", "M13", "M14", "M16"}:
        return True
    flipper = {"N": "S", "S": "N"}
    stop_time_update.stop_id = stop_id[:3] + flipper[stop_id[3]]
    return True


trip_data_cleaner = tripupdater.TripDataCleaner(
    [
        fix_route_ids,
        duplicate_stops_problem,
        delete_old_scheduled_trips,
        fix_current_stop_sequence
    ],
    [invert_j_train_direction_in_bushwick],
)


def route_ids_function(feed, route_ids):
    # TODO: this will eventually not be needed when Transiter source feature is made
    feed_id_to_routes = {
        '123456': ['1', '2', '3', '4', '5', '5X', '6', '6X', 'GS'],
        'JZ': ['J', 'Z'],
        'BDFM': ['B', 'D', 'F', 'M'],
        'ACE': ['A', 'C', 'E', 'H', 'FS'],
        'NQRW': ['N', 'Q', 'R', 'W'],
        'L': ['L'],
        'G': ['G'],
        'SIR': ['SI'],
        '7': ['7', '7X']
    }
    return feed_id_to_routes.get(feed.id, route_ids)


update = gtfsrealtimeutil.create_parser(
    gtfs_realtime_pb2,
    merge_in_nyc_subway_extension_data,
    trip_data_cleaner,
    route_ids_function,
)
