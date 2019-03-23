import copy
import datetime
import unittest
from unittest import mock
from transiter_nycsubway import gtfsupdater
from transiter import models


class TestUpdate(unittest.TestCase):

    def test_update__no_content_edge_case(self):
        actual = gtfsupdater.update(None, '')

        self.assertFalse(actual)


class TestMergeInExtensionData(unittest.TestCase):

    TRAIN_ID = "Train ID"
    DIRECTION_ID = False
    ACTUAL_TRACK = '1'
    SCHEDULED_TRACK = '2'
    STATUS_RUNNING = 'RUNNING'
    STATUS_SCHEDULED = 'SCHEDULED'

    def test_merge_in_trip_update(self):
        """[NYC Subway extension] Merge in trip update data"""
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': 'NORTH',
            'is_assigned': True
        }
        nyct_trip_descriptor = mock.MagicMock()
        nyct_trip_descriptor.get.side_effect = lambda x, y: nyct_trip_descriptor_dict[x]

        nyct_stop_time_update_dict = {
            'actual_track': self.ACTUAL_TRACK,
            'scheduled_track': self.SCHEDULED_TRACK
        }
        nyct_stop_time_update = mock.MagicMock()
        nyct_stop_time_update.get.side_effect = lambda x, y: nyct_stop_time_update_dict[x]

        input_data = {
            'header': {
                'nyct_feed_header': nyct_feed_header
            },
            'entity': [
                {
                    'trip_update': {
                        'trip': {
                            'nyct_trip_descriptor': nyct_trip_descriptor
                        },
                        'stop_time_update': [
                            {
                                'nyct_stop_time_update': nyct_stop_time_update
                            }
                        ]
                    }
                }
            ]
        }

        expected_output_data = {
            'header': {},
            'entity': [
                {
                    'trip_update': {
                        'trip': {
                            'direction_id': self.DIRECTION_ID,
                        },
                        'vehicle': {
                            'id': self.TRAIN_ID,
                        },
                        'stop_time_update': [
                            {
                                'track': self.ACTUAL_TRACK
                            }
                        ]
                    }
                }
            ]
        }

        actual_output_data = gtfsupdater.merge_in_nyc_subway_extension_data(
            input_data)

        self.maxDiff = None
        self.assertDictEqual(expected_output_data, actual_output_data)

    def test_merge_in_vehicle(self):
        """[NYC Subway extension] Merge in vehicle data"""
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': None,
            'is_assigned': False
        }
        nyct_trip_descriptor = mock.MagicMock()
        nyct_trip_descriptor.get.side_effect = lambda x, y: nyct_trip_descriptor_dict[x]

        nyct_stop_time_update_dict = {
            'actual_track': None,
            'scheduled_track': self.SCHEDULED_TRACK
        }
        nyct_stop_time_update = mock.MagicMock()
        nyct_stop_time_update.get.side_effect = lambda x, y: nyct_stop_time_update_dict[x]

        input_data = {
            'header': {
                'nyct_feed_header': nyct_feed_header
            },
            'entity': [
                {
                    'vehicle': {
                        'trip': {
                            'nyct_trip_descriptor': nyct_trip_descriptor
                        },
                    }
                }
            ]
        }

        expected_output_data = {
            'header': {},
            'entity': [
                {
                    'vehicle': { # This is the VehiclePosition
                        'trip': {},
                        'vehicle': { # This is the VehicleDescriptor
                            'id': self.TRAIN_ID,
                        }
                            #'direction_id': None,
                            #'status': self.STATUS_SCHEDULED
                        #},
                    }
                }
            ]
        }

        actual_output_data = gtfsupdater.merge_in_nyc_subway_extension_data(
            input_data)

        self.maxDiff = None
        self.assertDictEqual(expected_output_data, actual_output_data)


class TestNycSubwayGtfsCleaner(unittest.TestCase):

    def test_fix_route_ids_5x(self):
        """[NYC Subway cleaner] Fix 5X route IDs"""
        trip = models.Trip()
        trip.route_id = '5X'

        response = gtfsupdater.fix_route_ids(trip)

        self.assertTrue(response)
        self.assertEqual('5', trip.route_id)

    def test_fix_route_ids_no_route_id(self):
        """[NYC Subway cleaner] Delete trips without route Ids"""
        trip = models.Trip()
        trip.route_id = ''

        response = gtfsupdater.fix_route_ids(trip)

        self.assertFalse(response)

    def test_fix_route_ids_ss(self):
        """[NYC Subway cleaner] Delete trips with route_id=SS"""
        trip = models.Trip()
        trip.route_id = 'SS'

        response = gtfsupdater.fix_route_ids(trip)

        self.assertFalse(response)

    def test_fix_route_ids_good_route(self):
        """[NYC Subway cleaner] Delete trips with route_id=SS - no delete case"""
        trip = models.Trip()
        trip.route_id = 'A'

        response = gtfsupdater.fix_route_ids(trip)

        self.assertTrue(response)

    def test_delete_old_scheduled_trips_delete(self):
        """[NYC Subway cleaner] Delete old scheduled trips that haven't started"""
        trip = models.Trip()
        trip.start_time = datetime.datetime.fromtimestamp(100)
        trip.current_status = 'SCHEDULED'

        cleaner = gtfsupdater.delete_old_scheduled_trips(
            datetime.datetime.fromtimestamp(1000))
        response = cleaner(trip)

        self.assertFalse(response)

    def test_delete_old_scheduled_trips_started(self):
        """[NYC Subway cleaner] Don't delete scheduled trips that have started"""
        trip = models.Trip()
        trip.start_time = datetime.datetime.fromtimestamp(100)
        trip.current_status = 'RUNNING'

        cleaner = gtfsupdater.delete_old_scheduled_trips(
            datetime.datetime.fromtimestamp(1000))
        response = cleaner(trip)

        self.assertTrue(response)

    def test_delete_old_scheduled_trips_not_old(self):
        """[NYC Subway cleaner] Don't delete scheduled trips that aren't old"""
        trip = models.Trip()
        trip.start_time = datetime.datetime.fromtimestamp(1000)
        trip.current_status = 'SCHEDULED'

        cleaner = gtfsupdater.delete_old_scheduled_trips(
            datetime.datetime.fromtimestamp(1000))
        response = cleaner(trip)

        self.assertTrue(response)

    def test_invert_j_train_direction_in_bushwick(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick N->S"""
        stop_time_update = models.StopTimeUpdate()
        stop_time_update.stop_id = 'M12N'
        trip = models.Trip()
        trip.route_id = 'J'
        trip.stop_events.append(stop_time_update)

        gtfsupdater.invert_j_train_direction_in_bushwick(stop_time_update)

        self.assertEqual('M12S', stop_time_update.stop_id)

    def test_invert_j_train_direction_in_bushwick_two(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick S->N"""
        stop_time_update = models.StopTimeUpdate()
        stop_time_update.stop_id = 'M12S'
        trip = models.Trip()
        trip.route_id = 'J'
        trip.stop_events.append(stop_time_update)

        gtfsupdater.invert_j_train_direction_in_bushwick(stop_time_update)

        self.assertEqual('M12N', stop_time_update.stop_id)

    def test_invert_j_train_direction_in_bushwick_irrelevant_stop(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick, irrelevant stop"""
        stop_time_update = models.StopTimeUpdate()
        stop_time_update.stop_id = 'M20N'
        trip = models.Trip()
        trip.route_id = 'J'
        trip.stop_events.append(stop_time_update)

        gtfsupdater.invert_j_train_direction_in_bushwick(stop_time_update)

        self.assertEqual('M20N', stop_time_update.stop_id)

    def test_invert_j_train_direction_in_bushwick_irrelevant_route(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick, irrelevant route"""
        stop_time_update = models.StopTimeUpdate()
        stop_time_update.stop_id = 'M12N'
        trip = models.Trip()
        trip.route_id = 'A'
        trip.stop_events.append(stop_time_update)

        gtfsupdater.invert_j_train_direction_in_bushwick(stop_time_update)

        self.assertEqual('M12N', stop_time_update.stop_id)

    DATETIME_1 = datetime.datetime(2018, 11, 5, 13, 0, 0)
    DATETIME_2 = datetime.datetime(2018, 11, 5, 13, 0, 10)
    DATETIME_3 = datetime.datetime(2018, 11, 5, 13, 0, 20)
    DATETIME_4 = datetime.datetime(2018, 11, 5, 13, 0, 30)

    def test_delete_first_stop_event_slow_updating_trips__one_stop_id(self):
        """[NYC Subway cleaner] Delete slow updating trips - one stop case"""
        stop_time_update = models.StopTimeUpdate()
        trip = models.Trip()
        trip.stop_events.append(stop_time_update)

        gtfsupdater.delete_first_stu_in_slow_updating_trips(trip)

        self.assertEqual([stop_time_update], trip.stop_events)

    def test_delete_first_stop_event_slow_updating_trips__no_update_time(self):
        """[NYC Subway cleaner] Delete slow updating trips - no update time"""
        stu_1 = models.StopTimeUpdate(stop_sequence=1)
        stu_2 = models.StopTimeUpdate(stop_sequence=2)
        trip = models.Trip()
        trip.last_update_time = None
        trip.stop_events.extend([stu_1, stu_2])

        gtfsupdater.delete_first_stu_in_slow_updating_trips(trip)

        self.assertEqual([stu_1, stu_2], trip.stop_events)

    def test_delete_first_stop_event_slow_updating_trips__first_stop_in_the_future(
            self):
        """[NYC Subway cleaner] Delete slow updating trips - first stop in the future"""
        stu_1 = models.StopTimeUpdate(stop_sequence=1, departure_time=self.DATETIME_4)
        stu_2 = models.StopTimeUpdate(stop_sequence=2)
        trip = models.Trip()
        trip.last_update_time = self.DATETIME_1
        trip.stop_events.extend([stu_1, stu_2])

        gtfsupdater.delete_first_stu_in_slow_updating_trips(trip)

        self.assertEqual([stu_1, stu_2], trip.stop_events)

    def test_delete_first_stop_event_slow_updating_trips__stale(self):
        """[NYC Subway cleaner] Delete slow updating trips - stale data"""
        stu_1 = models.StopTimeUpdate(stop_sequence=1, departure_time=self.DATETIME_1)
        stu_2 = models.StopTimeUpdate(stop_sequence=2)
        trip = models.Trip()
        trip.last_update_time = self.DATETIME_4
        trip.stop_events.extend([stu_1, stu_2])

        gtfsupdater.delete_first_stu_in_slow_updating_trips(trip)

        self.assertEqual([stu_2], trip.stop_events)

    def test_transform_basic_data(self):
        second = 30
        minute = 23
        hour = 3
        day = 13
        month = 2
        year = 2017
        start_date = '{:04d}{:02d}{:02d}'.format(year, month, day)
        trip_id = '{:06d}_IGNORED'.format(((hour*3600+minute*60+second)*10)//6)

        trip = models.Trip()
        trip.direction_id = True
        trip.id = trip_id
        trip.route_id = 'L'
        trip.start_time = datetime.datetime(year, month, day, 0, 0, 0)

        expected_start_time = datetime.datetime(year, month, day, hour, minute, second)

        gtfsupdater.transform_basic_data(trip)

        self.assertEqual(expected_start_time, trip.start_time)
        self.assertEqual('LS'+str(int(expected_start_time.timestamp())), trip.id)


