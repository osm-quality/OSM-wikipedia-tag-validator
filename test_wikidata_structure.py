import unittest
from wikibrain import wikimedia_link_issue_reporter
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import common
import osm_handling_config.global_config as osm_handling_config

class WikidataTests(unittest.TestCase):
    def is_unlinkable_check(self, type_id):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_error_report_if_type_unlinkable_as_primary(type_id)

    def dump_debug_into_stdout(self, type_id):
        is_unlinkable = self.is_unlinkable_check(type_id)
        wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().dump_base_types_of_object_in_stdout(type_id, 'tests')
        print()
        if is_unlinkable != None:
            print(is_unlinkable.error_message)

    def assert_linkability(self, type_id):
        is_unlinkable = self.is_unlinkable_check(type_id)
        if is_unlinkable != None:
            self.dump_debug_into_stdout(type_id)
        self.assertEqual(None, is_unlinkable)

    def assert_unlinkability(self, type_id):
        is_unlinkable = self.is_unlinkable_check(type_id)
        if is_unlinkable == None:
            self.dump_debug_into_stdout(type_id)
        self.assertNotEqual(None, is_unlinkable)

    def test_rejects_links_to_events(self):
        self.assert_unlinkability('Q134301')

    def test_rejects_links_to_spacecraft(self):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        self.assertNotEqual(None, wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_error_report_if_property_indicates_that_it_is_unlinkable_as_primary('Q2513'))

    def test_reject_links_to_humans(self):
        self.assert_unlinkability('Q561127')

    def test_detecting_makro_as_invalid_primary_link(self):
        self.assert_unlinkability('Q704606')

    def test_detecting_tesco_as_invalid_primary_link(self):
        self.assert_unlinkability('Q487494')

    def test_detecting_carrefour_as_invalid_primary_link(self):
        self.assert_unlinkability('Q217599')

    def test_detecting_cropp_as_invalid_primary_link(self):
        self.assert_unlinkability('Q9196793')

    def test_detecting_castle_as_valid_primary_link(self):
        self.assert_linkability('Q2106892')

    def test_detecting_funicular_as_valid_primary_link(self):
        self.assert_linkability('Q5614426')

    def test_detecting_fast_tram_as_valid_primary_link(self):
        self.assert_linkability('Q1814872')

    def test_detecting_high_school_as_valid_primary_link(self):
        self.assert_linkability('Q9296000')

    def test_detecting_primary_school_as_valid_primary_link(self):
        self.assert_linkability('Q7112654')

    def test_detecting_fountain_as_valid_primary_link(self):
        self.assert_linkability('Q992764')

    def test_detecting_wastewater_plant_as_valid_primary_link(self):
        self.assert_linkability('Q11795812')

    def test_detecting_burough_as_valid_primary_link(self):
        self.assert_linkability('Q1630')
