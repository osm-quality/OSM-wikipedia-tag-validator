import unittest
import wikipedia_validator
import common
import wikipedia_connection

class Tests(unittest.TestCase):
    def test_vents_are_unlinkable_as_primary_tags(self):
        wikipedia_connection.set_cache_location(common.get_file_storage_location())
        self.assertNotEqual(None, wikipedia_validator.get_error_report_if_type_unlinkable_as_primary('Q134301'))

if __name__ == '__main__':
    unittest.main()