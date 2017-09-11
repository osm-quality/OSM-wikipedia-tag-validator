import unittest
import wikipedia_validator
import common
import osm_iterator
import wikipedia_connection
import generate_osm_edits
import generate_webpage_with_error_output
import generate_overpass_query_output
import script

class Tests(unittest.TestCase):
    def test_vents_are_unlinkable_as_primary_tags(self):
        wikipedia_connection.set_cache_location(common.get_file_storage_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary('Q134301'))

if __name__ == '__main__':
    unittest.main()
