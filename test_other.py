import unittest
import wikipedia_validator
import wikidata_processing
import common
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import generate_webpage_with_error_output
import generate_overpass_query_output
import script
import osm_handling_config.global_config as osm_handling_config

class Tests(unittest.TestCase):
    def test_complain_function(self):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        wikipedia_validator.complain_in_stdout_if_wikidata_entry_not_of_known_safe_type('Q824359', "explanation")

    def test_get_prerequisite_in_overpass_query_format(self):
        self.assertEqual(common.get_prerequisite_in_overpass_query_format({'prerequisite': {}}), "")

    def test_description_of_distance_return_string(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(wikipedia_validator.get_distance_description_between_location_and_wikidata_id((50, 20), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(wikipedia_validator.get_distance_description_between_location_and_wikidata_id((None, None), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location_and_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(wikipedia_validator.get_distance_description_between_location_and_wikidata_id((None, None), example_artist_id)))

    def test_description_of_distance_return_string_for_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(wikipedia_validator.get_distance_description_between_location_and_wikidata_id((50, 20), example_artist_id)))

    def test_overpass_escaping(self):
        before = {'wikipedia:de': "Zapiekle, Pickel's Vorwerk"}
        after = "['wikipedia:de'='Zapiekle, Pickel\\'s Vorwerk']"
        print(before)
        print(common.tag_dict_to_overpass_query_format(before))
        print(before)
        self.assertEqual(after, common.tag_dict_to_overpass_query_format(before))

    def test_args_depending_code_for_behavior(self):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        #TODO - handle args. in test
        #wikipedia_validator.attempt_to_locate_wikipedia_tag_using_wikidata_id('Q2106892', False)

    def test_wikidata_ids_of_countries_with_language(self):
        self.assertEqual (['Q36'], wikipedia_validator.wikidata_ids_of_countries_with_language("pl"))
        self.assertEqual (('Q408' in wikipedia_validator.wikidata_ids_of_countries_with_language("en")), True)

if __name__ == '__main__':
    unittest.main()
