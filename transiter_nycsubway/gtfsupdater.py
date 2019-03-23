from transiter.services.update import tripupdater, gtfsrealtimeutil


def update(feed, content):
    if len(content) == 0:
        return False
    nyc_subway_gtfs_extension = gtfsrealtimeutil.GtfsRealtimeExtension(
        '..nyc_subway_pb2', __name__)
    gtfs_data = gtfsrealtimeutil.read_gtfs_realtime(content, nyc_subway_gtfs_extension)
    merge_in_nyc_subway_extension_data(gtfs_data)
    (feed_time, route_ids, trips) = gtfsrealtimeutil.transform_to_transiter_structure(
        gtfs_data, 'America/New_York')
    trip_data_cleaner = tripupdater.TripDataCleaner(
        [transform_basic_data,
         fix_route_ids,
         delete_old_scheduled_trips(feed_time),
         delete_first_stu_in_slow_updating_trips],
        [invert_j_train_direction_in_bushwick]
    )
    cleaned_trips = trip_data_cleaner.clean(trips)
    tripupdater.sync_trips(feed.system, route_ids, cleaned_trips)


def merge_in_nyc_subway_extension_data(data):
    data['header'].pop('nyct_feed_header', None)

    for entity in data['entity']:
        stop_time_updates = []
        trip = None
        if 'trip_update' in entity:
            main_entity = entity['trip_update']
            #trip = entity['trip_update']['trip']
            stop_time_updates = entity['trip_update']['stop_time_update']
        elif 'vehicle' in entity:
            main_entity = entity['vehicle']
            #trip = entity['vehicle']['trip']
        else:
            continue
        trip = main_entity['trip']

        nyct_trip_data = trip.get('nyct_trip_descriptor', {})

        train_id = nyct_trip_data.get('train_id', None)
        if train_id is not None:
            main_entity['vehicle'] = {
                'id': train_id
            }

        direction = nyct_trip_data.get('direction', None)
        if direction is not None:
            trip['direction_id'] = (direction == 'SOUTH')

        if 'vehicle' in entity:
            if nyct_trip_data.get('is_assigned', False):
                entity['current_status'] = 'SCHEDULED'

        del trip['nyct_trip_descriptor']

        for stop_time_update in stop_time_updates:
            nyct_stop_event_data = stop_time_update.get('nyct_stop_time_update', None)
            if nyct_stop_event_data is None:
                continue

            stop_time_update['track'] = nyct_stop_event_data.get(
                'actual_track', nyct_stop_event_data.get('scheduled_track', None))
            del stop_time_update['nyct_stop_time_update']

    return data


def transform_basic_data(trip):
    try:
        # The time is encoded in hundreths of a minute after midnight
        # according to MTA documentation
        time_string = trip.id[:trip.id.find('_')]
        seconds_since_midnight = (int(time_string)//10)*6
        trip.start_time = trip.start_time.replace(
            second=seconds_since_midnight % 60,
            minute=(seconds_since_midnight // 60) % 60,
            hour=(seconds_since_midnight // 3600))

        # The MTA trip id is not guaranteed to be invariant so we transform
        # it to something invariant
        if trip.direction_id:
            direction = 'S'
        else:
            direction = 'N'
        trip.id = trip.route_id + direction + str(int(trip.start_time.timestamp()))
        return True
    except Exception as e:
        # TODO: PyCharm is right: classify the exceptions that can occur here
        #print('Could not parse {}'.format(trip.id))
        return False


def fix_route_ids(trip):
    if trip.route_id == '5X':
        trip.route_id = '5'
    if trip.route_id == '' or trip.route_id == 'SS':
        return False
    return True


def delete_old_scheduled_trips(reference_time):

    def trip_cleaner(trip):
        if trip.current_status != 'SCHEDULED':
            return True
        if (reference_time - trip.start_time).total_seconds() > 300:
            return False
        return True

    return trip_cleaner


def delete_first_stu_in_slow_updating_trips(trip):
    if len(trip.stop_events) < 2:
        return True
    if trip.last_update_time is None:
        return True

    first_stu = trip.stop_events[0]
    if first_stu.arrival_time is not None:
        first_stop_time = first_stu.arrival_time
    else:
        first_stop_time = first_stu.departure_time

    if trip.last_update_time is None or first_stop_time is None:
        print('Buggy')
        print(trip, trip.last_update_time, first_stop_time, trip.stop_events)
        return False

    if (trip.last_update_time - first_stop_time).total_seconds() > 15:
        trip.stop_events.pop(0)
    return True


# TODO: only apply this in the JZ feed
def invert_j_train_direction_in_bushwick(stop_time_update):
    route_id = stop_time_update.trip.route_id
    if route_id != 'J' and route_id != 'Z':
        return True
    stop_id = stop_time_update.stop_id
    if stop_id[:3] not in {'M11', 'M12', 'M13', 'M14', 'M16'}:
        return True
    flipper = {
        'N': 'S',
        'S': 'N'
    }
    stop_time_update.stop_id = stop_id[:3] + flipper[stop_id[3]]
    return True

