from transiter.utils import gtfsrealtimeutil
from transiter.services.update import tripupdater


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
        [invert_j_train_direction_in_bushwick])
    print('#T: {}'.format(len(trips)))
    cleaned_trips = trip_data_cleaner.clean(trips)
    tripupdater.sync_trips(feed.system, route_ids, cleaned_trips)


# TODO: everything except track should be merged into actual GTFS realtime feeds
def merge_in_nyc_subway_extension_data(data):
    data['header'].pop('nyct_feed_header', None)

    for entity in data['entity']:
        stop_time_updates = []
        trip = None
        if 'trip_update' in entity:
            trip = entity['trip_update']['trip']
            stop_time_updates = entity['trip_update']['stop_time_update']
        elif 'vehicle' in entity:
            trip = entity['vehicle']['trip']
        if trip is None:
            continue

        nyct_trip_data = trip['nyct_trip_descriptor']
        trip['train_id'] = nyct_trip_data.get('train_id', None)

        direction = nyct_trip_data.get('direction', None)
        if direction is None:
            trip['direction_id'] = None
        else:
            trip['direction_id'] = (direction == 'SOUTH')

        if nyct_trip_data.get('is_assigned', False):
            trip['status'] = 'RUNNING'
        else:
            trip['status'] = 'SCHEDULED'

        del trip['nyct_trip_descriptor']

        for stop_time_update in stop_time_updates:
            nyct_stop_event_data = stop_time_update.get('nyct_stop_time_update', None)
            if nyct_stop_event_data is None:
                continue

            stop_time_update['track'] = nyct_stop_event_data.get(
                'actual_track', nyct_stop_event_data.get('scheduled_track', None))
            del stop_time_update['nyct_stop_time_update']

    return data


"""


class _NycSubwayGtfsCleaner:

    def __init__(self):
        # TODO: trip data cleaner should be in the gtfsrealtimeutil?
        # OR tripupdateutil with sync_trips?
        # Either way, the cleaners should be input to the constructor
        self.trip_cleaners = [
            self.transform_trip_data,
            self.fix_route_ids,
            self.delete_old_scheduled_trips,
            self.delete_first_stop_event_slow_updating_trips,
            self.delete_trips_with_route_id_ss
        ]
        self.stop_event_cleaners = [
            self.invert_j_train_direction_in_bushwick
        ]
        self.data = None

    def clean(self, data):
        self.data = data
        trips_to_delete = set()
        for index, trip in enumerate(data.get('trips', [])):
            result = True
            for trip_cleaner in self.trip_cleaners:
                result = (result and trip_cleaner(trip))
                if not result:
                    trips_to_delete.add(index)
                    break
            if not result:
                continue

            for stop_event in trip['stop_events']:
                for stop_event_cleaner in self.stop_event_cleaners:
                    stop_event_cleaner(stop_event, trip)

        new_trips = []
        for index, trip in enumerate(data['trips']):
            if index not in trips_to_delete:
                new_trips.append(trip)

        data['trips'] = new_trips
        return data

    @staticmethod
    def transform_trip_data(trip):
        try:
            if trip['direction_id']:
                direction = 'S'
            else:
                direction = 'N'
            trip_uid = generate_trip_uid(
                trip['id'],
                trip['start_date'],
                trip['route_id'],
                direction
                )
            # TODO: the start time here should conform to the GTFS realtime spec instead of being a timestamp
            start_time = generate_trip_start_time(
                trip['id'], trip['start_date'])
            trip['start_time'] = start_time
            trip['id'] = trip_uid
            return True
        except Exception:
            return False

    @staticmethod
    def fix_route_ids(trip):
        if trip['route_id'] == '5X':
            trip['route_id'] = '5'
        if trip['route_id'] == '':
            return False
        return True

    def delete_old_scheduled_trips(self, trip):
        seconds_since_started = (self.data['timestamp'] - trip['start_time']).total_seconds()
        if trip['current_status'] == 'SCHEDULED' and seconds_since_started > 300:
            return False
        return True

    @staticmethod
    def delete_first_stop_event_slow_updating_trips(trip):
        if len(trip['stop_events'])>1:
            if trip['last_update_time'] is None:
                return True
            first_stop_time = trip['stop_events'][0]['arrival_time']
            if first_stop_time is None:
                first_stop_time = trip['stop_events'][0]['departure_time']
            if first_stop_time > trip['last_update_time']:
                return True
            # TODO: make this the feed time -> should be deterministic
            current_time = datetime.datetime.fromtimestamp(
                int(time.time()), datetime.timezone.utc)
            #current_time = timestamp_to_datetime(int(time.time()))
            seconds_since_update = (current_time - trip['last_update_time']).total_seconds()
            print(seconds_since_update)
            if seconds_since_update > 15:
                trip['stop_events'].pop(0)
        return True

    # TODO: only apply this in the JZ feed
    @staticmethod
    def invert_j_train_direction_in_bushwick(stop_event, trip):
        if trip['route_id'] != 'J' and trip['route_id'] != 'Z':
            return True
        stop_id_alias = stop_event.get('stop_id', None)
        if stop_id_alias[:3] not in {'M12', }:
            return True
        print(stop_id_alias)
        if stop_id_alias[3:] == 'N':
            direction = 'S'
        else:
            direction = 'N'
        stop_event['stop_id'] = stop_id_alias[:3] + direction
        return True

    @staticmethod
    def delete_trips_with_route_id_ss(trip):
        if trip['route_id'] == 'SS':
            return False
        return True


# TODO: this time zone spec should be in the config
eastern = pytz.timezone('US/Eastern')
def generate_trip_start_time(trip_id, start_date):
    # TODO: double check the following hocus pocus
    seconds_since_midnight = (int(trip_id[:trip_id.find('_')])//10)*6
    second = seconds_since_midnight % 60
    minute = (seconds_since_midnight // 60) % 60
    hour = (seconds_since_midnight // 3600)
    year = int(start_date[0:4])
    month = int(start_date[4:6])
    day = int(start_date[6:8])
    print(year, month, day, hour, minute, second)
    return eastern.localize(datetime.datetime(year, month, day, hour, minute, second))

# TODO: move this into the single cleaner that calls it
def generate_trip_uid(trip_id, start_date, route_id, direction):
    return route_id + direction + str(int(generate_trip_start_time(trip_id, start_date).timestamp()))



"""


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
        print('Could not parse {}'.format(trip.id))
        raise e
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

