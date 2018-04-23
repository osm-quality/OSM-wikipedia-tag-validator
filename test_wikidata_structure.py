import unittest
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import common
import wikipedia_validator

class WikidataTests(unittest.TestCase):
    def assert_linkability(self, type_id):
        is_unlinkable = wikipedia_validator.get_error_report_if_type_unlinkable_as_primary(type_id)
        if is_unlinkable != None:
            wikipedia_validator.dump_base_types_of_object_in_stdout(type_id, 'tests')
            print()
            print(is_unlinkable.error_message)
        self.assertEqual(None, is_unlinkable)

    def test_rejects_links_to_events(self):
        wikimedia_connection.set_cache_location(common.get_wikimedia_connection_cache_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary('Q134301'))

    def test_rejects_links_to_spacecraft(self):
        wikimedia_connection.set_cache_location(common.get_wikimedia_connection_cache_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_property_indicates_that_it_is_unlinkable_as_primary('Q2513'))

    def test_reject_links_to_humans(self):
        example_artist_id = 'Q561127'
        location = None
        forced_refresh = False
        self.assertNotEqual(None, wikipedia_validator.get_problem_based_on_wikidata_base_types(location, example_artist_id, forced_refresh))

    def test_detecting_makro_as_invalid_primary_link(self):
        wikidata_id = 'Q704606'
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary(wikidata_id))

    def test_detecting_tesco_as_invalid_primary_link(self):
        wikidata_id = 'Q487494'
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary(wikidata_id))

    def test_detecting_carrefour_as_invalid_primary_link(self):
        wikidata_id = 'Q217599'
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary(wikidata_id))

    def test_detecting_cropp_as_invalid_primary_link(self):
        wikidata_id = 'Q9196793'
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary(wikidata_id))

    def test_detecting_castle_as_valid_primary_link(self):
        self.assert_linkability('Q2106892')

    def test_detecting_funicular_as_valid_primary_link(self):
        self.assert_linkability('Q5614426')

    def test_detecting_fast_tram_as_valid_primary_link(self):
        self.assert_linkability('Q1814872')
