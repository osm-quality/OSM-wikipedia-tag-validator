import unittest
import popular_wikidata_property_detector

class Tests(unittest.TestCase):
    def test_empty_run_of_property_counter(self):
        empty = popular_wikidata_property_detector.PopularWikidataPropertiesDetector()
        empty.print_popular_properties()

    def test_dummy_run_of_property_counter(self):
        dummy = popular_wikidata_property_detector.PopularWikidataPropertiesDetector()
        dummy.record_property_presence('dummy')
        dummy.record_property_presence('dummy')
        dummy.record_property_presence('dummy')
        dummy.record_property_presence('dummy')
        dummy.record_property_presence('dummy2')
        dummy.record_property_presence('dummy3')
        dummy.print_popular_properties()