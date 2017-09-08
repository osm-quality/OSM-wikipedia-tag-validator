import unittest

class EmptyTest(unittest.TestCase):
    def test_empty_test_function(self):
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()