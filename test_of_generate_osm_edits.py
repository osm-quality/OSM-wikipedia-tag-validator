import unittest
import generate_osm_edits

class Tests(unittest.TestCase):
    def test_filter_reported_errors_on_empty_input(self):
        self.assertEqual([], generate_osm_edits.filter_reported_errors([], []))

    def test_filter_reported_errors_on_empty_ids(self):
        error = {'error_id': 'foobar'}
        self.assertEqual([], generate_osm_edits.filter_reported_errors([error], []))

    def test_filter_reported_errors_on_empty_items(self):
        self.assertEqual([], generate_osm_edits.filter_reported_errors([], ['example_id']))

    def test_filter_reported_errors_on_nonempty_return(self):
        error = {'error_id': 'foobar'}
        self.assertEqual([error], generate_osm_edits.filter_reported_errors([error], ['foobar']))
