import enum
import sys

from transiter.parse import GtfsRealtimeParser
from transiter.parse.gtfsrealtime import TRANSITER_EXTENSION_ID
from transiter_ny_mta.proto import subwaytrips_pb2 as gtfs_rt_pb2


class SubwayTripsParser(GtfsRealtimeParser):

    GTFS_REALTIME_PB2_MODULE = gtfs_rt_pb2

    @staticmethod
    def post_process_feed_message(feed_message):
        _move_data_between_extensions(feed_message)


class _MtaDirection(enum.Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


def _move_data_between_extensions(feed_message):
    for entity in feed_message.entity:
        for key in ["trip_update", "vehicle"]:
            if not entity.HasField(key):
                continue
            sub_entity = getattr(entity, key)

            mta_ext = sub_entity.trip.Extensions[
                sub_entity.trip._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
            ]

            # Map the MTA's direction onto the GTFS direction ID
            if not sub_entity.trip.HasField("direction_id"):
                if mta_ext.HasField("direction"):
                    direction_id = (
                        _MtaDirection(mta_ext.direction) == _MtaDirection.SOUTH
                    )
                else:
                    # NOTE: it seems the NYCT direction is NORTH if it's missing.
                    # It may be more robust to infer it from the trip ID, but this has
                    # apparently worked for multiple years...
                    direction_id = False
                sub_entity.trip.direction_id = direction_id

            # Map the MTA's train ID onto the GTFS vehicle ID.
            # Only do this if the trip has a train assigned
            if mta_ext.HasField("is_assigned"):
                is_assigned = mta_ext.is_assigned
            else:
                is_assigned = False
            if not sub_entity.HasField("vehicle") and is_assigned:
                sub_entity.vehicle.id = _create_vehicle_id_from_trip_desc(
                    mta_ext, sub_entity.trip.trip_id
                )

        if not entity.HasField("trip_update"):
            continue
        for stop_time in entity.trip_update.stop_time_update:
            mta_ext = stop_time.Extensions[
                stop_time._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
            ]
            if mta_ext.HasField("actual_track"):
                track = mta_ext.actual_track
            elif mta_ext.HasField("scheduled_track"):
                track = mta_ext.scheduled_track
            else:
                track = None

            transiter_ext = stop_time.Extensions[
                stop_time._extensions_by_number[TRANSITER_EXTENSION_ID]
            ]
            transiter_ext.track = track


def _create_vehicle_id_from_trip_desc(mta_ext, trip_id):
    if mta_ext.HasField("train_id"):
        return mta_ext.train_id
    else:
        return "vehicle_" + trip_id


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        content = f.read()
    parser = SubwayTripsParser()
    parser.load_content(content)
    parser.print()
