import unittest
import osm_editor_bot_for_approved_tasks

class Tests(unittest.TestCase):
    def test_filter_reported_errors_on_empty_input(self):
        self.assertEqual([], osm_editor_bot_for_approved_tasks.filter_reported_errors([], []))

    def test_filter_reported_errors_on_empty_ids(self):
        error = {'error_id': 'foobar'}
        self.assertEqual([], osm_editor_bot_for_approved_tasks.filter_reported_errors([error], []))

    def test_filter_reported_errors_on_empty_items(self):
        self.assertEqual([], osm_editor_bot_for_approved_tasks.filter_reported_errors([], ['example_id']))

    def test_filter_reported_errors_on_nonempty_return(self):
        error = {'error_id': 'foobar'}
        self.assertEqual([error], osm_editor_bot_for_approved_tasks.filter_reported_errors([error], ['foobar']))

    def test_polish_mountain_is_in_poland(self):
        self.assertEqual("pl", osm_editor_bot_for_approved_tasks.get_nominatim_country_code(49.5980495, 19.5937181)) # https://www.openstreetmap.org/node/478073419#map=15/49.5961/19.6076
