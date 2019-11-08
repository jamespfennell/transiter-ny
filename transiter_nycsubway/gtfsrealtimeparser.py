#
# (c) James Fennell 2019. Released under the MIT License.
#
"""
Module that provides the parser for the NYC Subway's GTFS Realtime feeds.
"""
import datetime

from transiter.services.update import gtfsrealtimeparser

# NOTE: even though not used, the NYCT protobuf file must be imported.
# It works by modifying the original gtfs_realtime_pb2 file.
# noinspection PyUnresolvedReferences
from transiter_nycsubway.gtfs import gtfs_realtime_pb2, nyct_subway_pb2


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
def duplicate_stops_problem(trip):

    stop_ids = set()
    for stop_time in trip.stop_times:
        if stop_time.stop_id in stop_ids:
            return False

    return True


def fix_route_ids(trip):
    if trip.route_id == "5X":
        trip.route_id = "5"
    if trip.route_id == "" or trip.route_id == "SS":
        return False
    return True


def delete_old_scheduled_trips(trip):
    if trip.current_status != "SCHEDULED":
        return True
    if (datetime.datetime.now() - trip.start_time).total_seconds() > 300:
        return False
    return True


def fix_current_stop_sequence(trip):
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


def invert_m_train_direction_in_bushwick(stop_time_update):
    route_id = stop_time_update.trip.route_id
    if route_id != "M":
        return True
    stop_id = stop_time_update.stop_id
    if stop_id[:3] not in {"M11", "M12", "M13", "M14", "M16", "M18"}:
        return True
    flipper = {"N": "S", "S": "N"}
    stop_time_update.stop_id = stop_id[:3] + flipper[stop_id[3]]
    return True


base_parser = gtfsrealtimeparser.create_parser(
    gtfs_realtime_pb2, merge_in_nyc_subway_extension_data
)

trip_data_cleaner = gtfsrealtimeparser.TripDataCleaner(
    [
        fix_route_ids,
        duplicate_stops_problem,
        delete_old_scheduled_trips,
        fix_current_stop_sequence,
    ],
    [invert_m_train_direction_in_bushwick],
)


def parse(binary_content, *args, **kwargs):
    return trip_data_cleaner.clean(base_parser(binary_content, *args, **kwargs))
