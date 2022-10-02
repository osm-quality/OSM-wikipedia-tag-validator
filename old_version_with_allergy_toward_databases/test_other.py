import unittest
import wikipedia_validator
import common
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import generate_webpage_with_error_output #validates syntax
import generate_overpass_query_output #validates syntax
import script #validates syntax
import osm_handling_config.global_config as osm_handling_config

class Tests(unittest.TestCase):
    def test_get_prerequisite_in_overpass_query_format(self):
        self.assertEqual(common.get_prerequisite_in_overpass_query_format({'prerequisite': {}}), "")

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

if __name__ == '__main__':
    unittest.main()
