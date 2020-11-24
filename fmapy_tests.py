import unittest


import fmap


class CacheTests(unittest.TestCase):
    def test_contains(self):
        c = fmap.Cache("path", [1, 2, 3])
        self.assertTrue(1 in c)
        self.assertFalse(0, c)


if __name__ == "__main__":
    unittest.main()
