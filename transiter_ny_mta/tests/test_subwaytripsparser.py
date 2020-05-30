import datetime

import pytest
import pytz
from transiter import parse
from transiter_ny_mta import SubwayTripsParser
from transiter_ny_mta.subwaytripsparser import _MtaDirection
from transiter_ny_mta.proto import subwaytrips_pb2 as gtfs

ALERT_ID = "alert_id"
TRIP_ID = "trip_id"
VEHICLE_ID = "vehicle_id"
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


def test_create_vehicle():
    pass


def test_create_vehicle__use_trip_id():
    pass


def test_create_vehicle__skip_unassigned_trip():
    # Test both explictely unassigned and missing
    pass


def test_create_vehicle__do_not_override():
    pass


def test_track():
    # Test 3 cases
    pass
