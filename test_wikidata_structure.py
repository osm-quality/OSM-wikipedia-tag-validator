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

    def test_reject_links_to_term_shopping(self):
        # https://www.openstreetmap.org/way/452123938
        self.assert_unlinkability('Q830036')


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

    def test_detecting_expressway_as_valid_primary_link(self):
        self.assert_linkability('Q5055176') # not an event

    def test_detecting_university_as_valid_primary_link(self):
        self.assert_linkability('Q1887879') # not a website (as "open access publisher" is using website, but is not a website)

    def test_detecting_university_as_valid_primary_link(self):
        self.assert_linkability('Q1887879') # not an event (via "education")

    def test_train_line_as_valid_primary_link(self):
        self.assert_linkability('Q3720557') # train service is not a service (Q15141321) defined as "transcation..."

    def test_tide_organ_as_valid_primary_link(self):
        self.assert_linkability('Q7975291') # art is not sublass of creativity - though it is using creativity. It is also not sublass of a process.

    def test_specific_event_center_as_valid_primary_link(self):
        self.assert_linkability('Q7414066')

    def test_park_as_valid_primary_link(self):
        self.assert_linkability('Q1535460') # cultural heritage ( https://www.wikidata.org/w/index.php?title=Q210272&action=history ) is not a subclass of heritage designation, heritage (https://www.wikidata.org/w/index.php?title=Q2434238&offset=&limit=500&action=history) is not subclass of preservation
        
    def test_geoglyph_as_valid_primary_link(self):
        self.assert_linkability('Q7717476') # not an event - via Q12060132 ("hell letter" that is not a signage, it is product of a signage)

    def test_dunes_as_valid_primary_link(self):
        self.assert_linkability('Q1130721') # not an event - aeolian landform (Q4687862) is not sublass of aeolian process, natural object is not sublass of natural phenonemon ( https://www.wikidata.org/w/index.php?title=Q29651224&action=history )

    def test_tree_as_valid_primary_link(self):
        self.assert_linkability('Q6703503') # not an event

    def test_wind_farm_as_valid_primary_link(self):
        self.assert_linkability('Q4102067') # not an event

    def test_hollywood_sign_as_valid_primary_link(self):
        self.assert_linkability('Q180376') # not an event (hollywood sign is not an instance of signage)

    def test_railway_segment_as_valid_primary_link(self):
        self.assert_linkability('Q2581240') # not a physical process

    def test_another_railway_segment_as_valid_primary_link(self):
        self.assert_linkability('Q1126676') # not a physical process

    def test_country_as_valid_primary_link(self):
        self.assert_linkability('Q30') # not an event

    def test_aqueduct_as_valid_primary_link(self):
        self.assert_linkability('Q2859225') # not an event

    def test_public_housing_as_valid_primary_link(self):
        self.assert_linkability('Q22329573') # not an event - aeolian landform (Q4687862) is not sublass of aeolian process

    def test_dry_lake_as_valid_primary_link(self):
        self.assert_linkability('Q1780699') # not an event

    def test_industrial_property_as_valid_primary_link(self):
        self.assert_linkability('Q5001422') # not an event

    def test_cemetery_as_valid_primary_link(self):
        self.assert_linkability('Q30593659') # not an event

    def test_megaproject_as_valid_primary_link(self):
        self.assert_linkability('Q782093') # some megaprojects are already existing, project ( https://www.wikidata.org/wiki/Q170584 ) may be already complete

    def test_pilgrim_route_as_valid_primary_link(self):
        self.assert_linkability('Q829469')
 
    def test_botanical_garden_as_valid_primary_link(self):
        self.assert_linkability('Q589884')
       
    def test_alley_as_valid_primary_link(self):
        self.assert_linkability('Q3413299')

    def test_zoo_as_valid_primary_link(self):
        self.assert_linkability('Q1886334')

    def test_public_aquarium_as_valid_primary_link(self):
        self.assert_linkability('Q4782760')

    def test_grave_as_valid_primary_link(self):
        self.assert_linkability('Q11789060')

    def test_monument_as_valid_primary_link(self):
        self.assert_linkability('Q11823211')

    def test_cafe_as_valid_primary_link(self):
        self.assert_linkability('Q672804')

    def test_religious_admininstrative_area_as_valid_primary_link(self):
        self.assert_linkability('Q1364786')

    def test_hiking_trail_as_valid_primary_link(self):
        self.assert_linkability('Q783074')
