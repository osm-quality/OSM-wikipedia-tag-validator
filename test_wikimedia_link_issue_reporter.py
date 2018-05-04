import unittest
import wikimedia_link_issue_reporter
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config

class Tests(unittest.TestCase):
    def issue_reporter(self):
        return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()

    def test_complain_function(self):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        self.issue_reporter().complain_in_stdout_if_wikidata_entry_not_of_known_safe_type('Q824359', "explanation")

    def test_description_of_distance_return_string(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(self.issue_reporter().get_distance_description_between_location_and_wikidata_id((50, 20), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(self.issue_reporter().get_distance_description_between_location_and_wikidata_id((None, None), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location_and_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(self.issue_reporter().get_distance_description_between_location_and_wikidata_id((None, None), example_artist_id)))

    def test_description_of_distance_return_string_for_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(self.issue_reporter().get_distance_description_between_location_and_wikidata_id((50, 20), example_artist_id)))

    def test_wikidata_ids_of_countries_with_language(self):
        self.assertEqual (['Q36'], self.issue_reporter().wikidata_ids_of_countries_with_language("pl"))
        self.assertEqual (('Q408' in self.issue_reporter().wikidata_ids_of_countries_with_language("en")), True)

    def test_that_completely_broken_wikipedia_tags_are_detected(self):
        self.assertEqual (True, self.issue_reporter().is_wikipedia_tag_clearly_broken("pl"))
        self.assertEqual (True, self.issue_reporter().is_wikipedia_tag_clearly_broken("polski:Smok"))

    def test_that_completely_broken_wikipedia_tag_detector_has_no_false_positives(self):
        self.assertEqual (False, self.issue_reporter().is_wikipedia_tag_clearly_broken("pl:smok"))

    def test_detector_of_old_style_wikipedia_links_accepts_valid(self):
        key = 'wikipedia:pl'
        self.assertEqual (True, self.issue_reporter().check_is_it_valid_key_for_old_style_wikipedia_tag(key))
        tags = {key: 'Kościół Najświętszego Serca Pana Jezusa'}
        self.assertEqual (None, self.issue_reporter().check_is_invalid_old_style_wikipedia_tag_present(tags, tags))

    def test_detector_of_old_style_wikipedia_links_refuses_invalid(self):
        key = 'wikipedia:fixme'
        self.assertEqual (False, self.issue_reporter().check_is_it_valid_key_for_old_style_wikipedia_tag(key))
        tags = {key: 'Kościół Najświętszego Serca Pana Jezusa'}
        self.assertNotEqual (None, self.issue_reporter().check_is_invalid_old_style_wikipedia_tag_present(tags, tags))

if __name__ == '__main__':
    unittest.main()
