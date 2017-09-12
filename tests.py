import unittest
import wikipedia_validator
import common
import osm_iterator
import wikipedia_connection
import generate_osm_edits
import generate_webpage_with_error_output
import generate_overpass_query_output
import script
import osm_iterator

class Tests(unittest.TestCase):
    def test_rejects_links_to_events(self):
        wikipedia_connection.set_cache_location(common.get_file_storage_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary('Q134301'))

    def test_rejects_links_to_spacecraft(self):
        wikipedia_connection.set_cache_location(common.get_file_storage_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_property_indicates_that_it_is_unlinkable_as_primary('Q2513'))

    def test_complain_function(self):
        wikipedia_connection.set_cache_location(common.get_file_storage_location())
        wikipedia_validator.complain_in_stdout_if_wikidata_entry_not_of_known_safe_type('Q824359', "explanation")

    def test_get_prerequisite_in_overpass_query_format(self):
        self.assertEqual(common.get_prerequisite_in_overpass_query_format({'prerequisite': {}}), "")

    def test_osm_iterator(self):
        from io import BytesIO
        some_file_or_file_like_object = BytesIO(b'<?xml version="1.0" encoding="UTF-8"?><osm><node id="17658600" lat="49.8698080" lon="8.6300980"></node></osm>')
        print(osm_iterator.Data(some_file_or_file_like_object).data)
        for element in osm_iterator.Data(some_file_or_file_like_object).data.getiterator():
            print("XXYXYXYXY" + " " + str(element.tag))

if __name__ == '__main__':
    unittest.main()
