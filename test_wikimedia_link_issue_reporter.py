import unittest
import wikimedia_link_issue_reporter
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config

class Tests(unittest.TestCase):
    def test_complain_function(self):
        wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
        wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().complain_in_stdout_if_wikidata_entry_not_of_known_safe_type('Q824359', "explanation")

    def test_description_of_distance_return_string(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_distance_description_between_location_and_wikidata_id((50, 20), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location(self):
        example_city_wikidata_id = 'Q31487'
        self.assertEqual(type(""), type(wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_distance_description_between_location_and_wikidata_id((None, None), example_city_wikidata_id)))

    def test_description_of_distance_return_string_for_missing_location_and_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_distance_description_between_location_and_wikidata_id((None, None), example_artist_id)))

    def test_description_of_distance_return_string_for_missing_location_in_wikidata(self):
        example_artist_id = 'Q561127'
        self.assertEqual(type(""), type(wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_distance_description_between_location_and_wikidata_id((50, 20), example_artist_id)))

    def test_wikidata_ids_of_countries_with_language(self):
        self.assertEqual (['Q36'], wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().wikidata_ids_of_countries_with_language("pl"))
        self.assertEqual (('Q408' in wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().wikidata_ids_of_countries_with_language("en")), True)

    def test_that_completely_broken_wikipedia_tags_are_detected(self):
        self.assertEqual (True, wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().is_wikipedia_tag_clearly_broken("pl"))
        self.assertEqual (True, wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().is_wikipedia_tag_clearly_broken("polski:Smok"))

    def test_that_completely_broken_wikipedia_tag_detector_has_no_false_positives(self):
        self.assertEqual (False, wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().is_wikipedia_tag_clearly_broken("pl:smok"))

if __name__ == '__main__':
    unittest.main()
