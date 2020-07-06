import datetime

import pytest
import pytz
from transiter import parse
from transiter_ny_mta import alertsparser
from transiter_ny_mta.proto import alerts_pb2 as gtfs_rt_pb2

ALERT_ID = "alert_id"
TIME_1 = datetime.datetime.utcfromtimestamp(1000).replace(tzinfo=pytz.UTC)
TIME_2 = datetime.datetime.utcfromtimestamp(2000).replace(tzinfo=pytz.UTC)


@pytest.mark.parametrize("priority", iter(alertsparser.NyctBusPriority))
def test_base_cases(priority):
    informed_entity = gtfs_rt_pb2.EntitySelector()
    mta_ext_key = informed_entity._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
    informed_entity.Extensions[mta_ext_key].sort_order = "MTA:{}".format(priority.value)

    alert = gtfs_rt_pb2.Alert(informed_entity=[informed_entity])
    mta_ext_key = alert._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
    alert.Extensions[mta_ext_key].created_at = int(TIME_1.timestamp())
    alert.Extensions[mta_ext_key].updated_at = int(TIME_2.timestamp())
    alert.Extensions[mta_ext_key].alert_type = "unused"

    feed_message = gtfs_rt_pb2.FeedMessage(
        header=gtfs_rt_pb2.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs_rt_pb2.FeedEntity(id=ALERT_ID, alert=alert)],
    )
    parser = alertsparser.AlertsParser()
    parser.load_content(feed_message.SerializeToString())

    expected_alerts = [
        parse.Alert(
            id=ALERT_ID,
            effect=alertsparser.priority_to_effect.get(
                priority, parse.Alert.Effect.MODIFIED_SERVICE
            ),
            created_at=TIME_1,
            updated_at=TIME_2,
        )
    ]

    actual_alerts = list(parser.get_alerts())

    assert expected_alerts == actual_alerts


def test_missing_entity_selector():
    alert = gtfs_rt_pb2.Alert()

    feed_message = gtfs_rt_pb2.FeedMessage(
        header=gtfs_rt_pb2.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs_rt_pb2.FeedEntity(id=ALERT_ID, alert=alert)],
    )
    parser = alertsparser.AlertsParser()
    parser.load_content(feed_message.SerializeToString())

    expected_alerts = [
        parse.Alert(id=ALERT_ID, effect=parse.Alert.Effect.MODIFIED_SERVICE,)
    ]

    actual_alerts = list(parser.get_alerts())

    assert expected_alerts == actual_alerts


@pytest.mark.parametrize("priority_string", ["MTA:1000", "blah"])
def test_bad_priority_string(priority_string):
    informed_entity = gtfs_rt_pb2.EntitySelector()
    mta_ext_key = informed_entity._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
    informed_entity.Extensions[mta_ext_key].sort_order = priority_string

    alert = gtfs_rt_pb2.Alert(informed_entity=[informed_entity])

    feed_message = gtfs_rt_pb2.FeedMessage(
        header=gtfs_rt_pb2.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs_rt_pb2.FeedEntity(id=ALERT_ID, alert=alert)],
    )
    parser = alertsparser.AlertsParser()
    parser.load_content(feed_message.SerializeToString())

    expected_alerts = [
        parse.Alert(id=ALERT_ID, effect=parse.Alert.Effect.MODIFIED_SERVICE)
    ]

    actual_alerts = list(parser.get_alerts())

    assert expected_alerts == actual_alerts
