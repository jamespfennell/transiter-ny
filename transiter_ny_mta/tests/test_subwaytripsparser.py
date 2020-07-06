import datetime

import pytest
import pytz
from transiter import parse
from transiter_ny_mta import SubwayTripsParser
from transiter_ny_mta.proto import subwaytrips_pb2 as gtfs
from transiter_ny_mta.subwaytripsparser import _MtaDirection

ALERT_ID = "alert_id"
TRIP_ID = "trip_id"
VEHICLE_ID = "vehicle_id"
STOP_ID = "stop_id"
TRACK_1_ID = "track_1_id"
TRACK_2_ID = "track_2_id"
TIME_1 = datetime.datetime.utcfromtimestamp(1000).replace(tzinfo=pytz.UTC)
TIME_2 = datetime.datetime.utcfromtimestamp(2000).replace(tzinfo=pytz.UTC)


@pytest.mark.parametrize("existing_direction_id", [None, True, False])
@pytest.mark.parametrize(
    "mta_direction,expected_direction_id",
    [
        [_MtaDirection.SOUTH, True],
        [_MtaDirection.WEST, False],
        [_MtaDirection.EAST, False],
        [_MtaDirection.NORTH, False],
        [None, False],
    ],
)
def test_direction(existing_direction_id, mta_direction, expected_direction_id):
    trip = gtfs.TripDescriptor(trip_id=TRIP_ID)
    if existing_direction_id is not None:
        expected_direction_id = existing_direction_id
        trip.direction_id = expected_direction_id
    if mta_direction is not None:
        trip.Extensions[
            trip._extensions_by_number[gtfs.MTA_EXTENSION_ID]
        ].direction = mta_direction.value

    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id="1", trip_update=gtfs.TripUpdate(trip=trip))],
    )

    expected_trip = parse.Trip(id=TRIP_ID, direction_id=expected_direction_id)

    parser = SubwayTripsParser()
    parser.load_content(message.SerializeToString())
    actual_trips = list(parser.get_trips())

    assert [expected_trip] == actual_trips


@pytest.mark.parametrize(
    "entity_key,entity_type",
    [["trip_update", gtfs.TripUpdate], ["vehicle", gtfs.VehiclePosition]],
)
@pytest.mark.parametrize(
    "is_assigned,expect_vehicle", [[True, True], [False, False], [None, False]]
)
@pytest.mark.parametrize(
    "train_id,expected_vehicle_id",
    [[VEHICLE_ID, VEHICLE_ID], [None, "vehicle_" + TRIP_ID]],
)
def test_create_vehicle(
    entity_key, entity_type, is_assigned, expect_vehicle, train_id, expected_vehicle_id
):
    trip = gtfs.TripDescriptor(trip_id=TRIP_ID)
    mta_ext = trip.Extensions[trip._extensions_by_number[gtfs.MTA_EXTENSION_ID]]
    if train_id is not None:
        mta_ext.train_id = train_id
    if is_assigned is not None:
        mta_ext.is_assigned = is_assigned

    entity_key_to_entity = {entity_key: entity_type(trip=trip)}
    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id="1", **entity_key_to_entity)],
    )

    expected_vehicle = parse.Vehicle(id=expected_vehicle_id, trip_id=TRIP_ID)

    parser = SubwayTripsParser()
    parser.load_content(message.SerializeToString())
    actual_vehicles = list(parser.get_vehicles())

    if expect_vehicle:
        assert [expected_vehicle] == actual_vehicles
    else:
        if entity_type is gtfs.VehiclePosition:
            assert [parse.Vehicle(id=None, trip_id=TRIP_ID)] == actual_vehicles
        else:
            assert [] == actual_vehicles


@pytest.mark.parametrize(
    "scheduled_track,actual_track,expected_track",
    [
        [None, None, None],
        [None, TRACK_1_ID, TRACK_1_ID],
        [TRACK_1_ID, None, TRACK_1_ID],
        [TRACK_1_ID, TRACK_2_ID, TRACK_2_ID],
    ],
)
def test_track(scheduled_track, actual_track, expected_track):
    stop_time = gtfs.TripUpdate.StopTimeUpdate(stop_id=STOP_ID)
    mta_ext = stop_time.Extensions[
        stop_time._extensions_by_number[gtfs.MTA_EXTENSION_ID]
    ]
    if scheduled_track is not None:
        mta_ext.scheduled_track = scheduled_track
    if actual_track is not None:
        mta_ext.actual_track = actual_track

    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id="1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID),
                    stop_time_update=[stop_time],
                ),
            )
        ],
    )

    expected_trip = parse.Trip(
        id=TRIP_ID,
        direction_id=False,
        stop_times=[parse.TripStopTime(stop_id=STOP_ID, track=expected_track)],
    )

    parser = SubwayTripsParser()
    parser.load_content(message.SerializeToString())
    actual_trips = list(parser.get_trips())

    assert [expected_trip] == actual_trips


STOP_IDS_TO_INVERT = {"M11", "M12", "M13", "M14", "M16", "M18"}


@pytest.mark.parametrize(
    "route_id,stop_id,expected_stop_id",
    [
        ["M", f"{stop_id}{old_direction}", f"{stop_id}{new_direction}"]
        for stop_id in STOP_IDS_TO_INVERT
        for old_direction, new_direction in [["N", "S"], ["S", "N"]]
    ]
    + [
        ["J", f"{stop_id}{old_direction}", f"{stop_id}{old_direction}"]
        for stop_id in STOP_IDS_TO_INVERT
        for old_direction in ["S", "N"]
    ]
    + [
        ["M", f"M10{old_direction}", f"M10{old_direction}"]
        for old_direction in ["S", "N"]
    ],
)
def test_invert_stop_id_direction_in_bushwick(route_id, stop_id, expected_stop_id):
    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id="1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID, route_id=route_id),
                    stop_time_update=[gtfs.TripUpdate.StopTimeUpdate(stop_id=stop_id)],
                ),
            )
        ],
    )

    expected_trip = parse.Trip(
        id=TRIP_ID,
        route_id=route_id,
        direction_id=False,
        stop_times=[parse.TripStopTime(stop_id=expected_stop_id)],
    )

    parser = SubwayTripsParser()
    parser.load_content(message.SerializeToString())
    actual_trips = list(parser.get_trips())

    assert [expected_trip] == actual_trips


@pytest.mark.parametrize(
    "route_id,actual_route_id,valid_trip",
    [["5", "5", True], ["5X", "5", True], ["", "", False], ["SS", "", False]],
)
def test_fix_route_ids(route_id, actual_route_id, valid_trip):
    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id="1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID, route_id=route_id),
                ),
            )
        ],
    )

    expected_trip = parse.Trip(
        id=TRIP_ID, route_id=actual_route_id, direction_id=False,
    )

    parser = SubwayTripsParser()
    parser.load_content(message.SerializeToString())
    actual_trips = list(parser.get_trips())

    if valid_trip:
        assert [expected_trip] == actual_trips
    else:
        assert [] == actual_trips
