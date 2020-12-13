import enum
import os

from transiter.parse import Alert
from transiter.parse import gtfsrealtime

from .proto import alerts_pb2 as gtfs_rt_pb2


class NyctBusPriority(enum.Enum):
    UNKNOWN = 0
    NYCT_BUS_PRIORITY_NO_SCHEDULED_SERVICE = 1
    NYCT_BUS_PRIORITY_SUNDAY_SCHEDULE = 2
    NYCT_BUS_PRIORITY_SATURDAY_SCHEDULE = 3
    NYCT_BUS_PRIORITY_HOLIDAY_SERVICE = 4
    NYCT_BUS_PRIORITY_PLANNED_DETOUR = 5
    NYCT_BUS_PRIORITY_EXTRA_SERVICE = 6
    NYCT_BUS_PRIORITY_PLANNED_WORK = 7
    NYCT_BUS_PRIORITY_ON_OR_CLOSE = 8
    NYCT_BUS_PRIORITY_SLOW_SPEEDS = 9
    NYCT_BUS_PRIORITY_SOME_DELAYS = 10
    NYCT_BUS_PRIORITY_SPECIAL_EVENT = 11
    NYCT_BUS_PRIORITY_STATIONS_SKIPPED = 12
    NYCT_BUS_PRIORITY_DELAYS = 13
    NYCT_BUS_PRIORITY_EXPRESS_TO_LOCAL = 14
    NYCT_BUS_PRIORITY_SOME_REROUTES = 15
    NYCT_BUS_PRIORITY_DETOUR = 16
    NYCT_BUS_PRIORITY_LOCAL_TO_EXPRESS = 17
    NYCT_BUS_PRIORITY_SERVICE_CHANGE = 18
    NYCT_BUS_PRIORITY_TRAINS_REROUTED = 19
    NYCT_BUS_PRIORITY_PART_SUSPENDED = 20
    NYCT_BUS_PRIORITY_MULTIPLE_IMPACTS = 21
    NYCT_BUS_PRIORITY_SUSPENDED = 22


priority_to_cause = {}


priority_to_effect = {
    NyctBusPriority.NYCT_BUS_PRIORITY_NO_SCHEDULED_SERVICE: Alert.Effect.NO_SERVICE,
    NyctBusPriority.NYCT_BUS_PRIORITY_PLANNED_DETOUR: Alert.Effect.DETOUR,
    NyctBusPriority.NYCT_BUS_PRIORITY_EXTRA_SERVICE: Alert.Effect.ADDITIONAL_SERVICE,
    NyctBusPriority.NYCT_BUS_PRIORITY_SOME_DELAYS: Alert.Effect.SIGNIFICANT_DELAYS,
    NyctBusPriority.NYCT_BUS_PRIORITY_STATIONS_SKIPPED: Alert.Effect.REDUCED_SERVICE,
    NyctBusPriority.NYCT_BUS_PRIORITY_DELAYS: Alert.Effect.SIGNIFICANT_DELAYS,
    NyctBusPriority.NYCT_BUS_PRIORITY_DETOUR: Alert.Effect.DETOUR,
    NyctBusPriority.NYCT_BUS_PRIORITY_PART_SUSPENDED: Alert.Effect.REDUCED_SERVICE,
    NyctBusPriority.NYCT_BUS_PRIORITY_SUSPENDED: Alert.Effect.REDUCED_SERVICE,
}


class AlertsParser(gtfsrealtime.GtfsRealtimeParser):

    GTFS_REALTIME_PB2_MODULE = gtfs_rt_pb2

    def get_alerts(self):
        for alert in super().get_alerts():
            if _should_skip_alert(alert):
                continue
            yield alert

    @staticmethod
    def post_process_feed_message(feed_message):
        _move_data_between_extensions(feed_message)


_NON_ALERT_HEADERS = {
    "weekend service",
    "weekday service",
}


def _should_skip_alert(alert) -> bool:
    if os.environ.get("TRANSITER_NY_MTA_KEEP_NON_ALERTS") == "true":
        return False
    for message in alert.messages:
        if message.header.strip().lower() in _NON_ALERT_HEADERS:
            return True
    return False


def _move_data_between_extensions(feed_message):
    for entity in feed_message.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        mta_ext_key = alert._extensions_by_number[gtfs_rt_pb2.MTA_EXTENSION_ID]
        transiter_ext_key = alert._extensions_by_number[
            gtfsrealtime.TRANSITER_EXTENSION_ID
        ]
        if alert.Extensions[mta_ext_key].HasField("created_at"):
            alert.Extensions[transiter_ext_key].created_at = alert.Extensions[
                mta_ext_key
            ].created_at
        if alert.Extensions[mta_ext_key].HasField("updated_at"):
            alert.Extensions[transiter_ext_key].updated_at = alert.Extensions[
                mta_ext_key
            ].updated_at

        if len(alert.informed_entity) == 0:
            alert.effect = Alert.Effect.MODIFIED_SERVICE.value
            continue
        informed_entity = alert.informed_entity[0]
        mta_ext_key = informed_entity._extensions_by_number[
            gtfs_rt_pb2.MTA_EXTENSION_ID
        ]
        sort_order = informed_entity.Extensions[mta_ext_key].sort_order
        priority_val_string = sort_order[sort_order.rfind(":") + 1 :]
        priority = _convert_priority_val_string_to_priority(priority_val_string)
        alert.cause = priority_to_cause.get(priority, Alert.Cause.UNKNOWN_CAUSE).value
        alert.effect = priority_to_effect.get(
            priority, Alert.Effect.MODIFIED_SERVICE
        ).value


def _convert_priority_val_string_to_priority(
    priority_val_string: str,
) -> NyctBusPriority:
    try:
        priority_val = int(priority_val_string)
    except ValueError:
        return NyctBusPriority.UNKNOWN
    try:
        return NyctBusPriority(priority_val)
    except ValueError:
        return NyctBusPriority.UNKNOWN
