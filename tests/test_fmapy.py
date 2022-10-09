from .context import fmapy

import unittest
import unittest.mock


SEARCH_URL = fmapy.SEARCH_URL


class FmapyTests(unittest.TestCase):
    def test_get_search_base_url(self):
        self.assertEqual(SEARCH_URL, fmapy.get_search_base_url())

    def test_get_search_url(self):
        term = "song"
        self.assertEqual(SEARCH_URL + "song", fmapy.get_search_url(term))

        term = "best song"
        self.assertEqual(SEARCH_URL + "best+song", fmapy.get_search_url(term))

    @unittest.mock.patch("requests.get")
    def test_do_search(self, mock_get):
        term = "mock song"
        url = fmapy.get_search_url(term)

        with unittest.mock.patch("fmapy.core.get_search_url") as mock_url:
            mock_url.return_value = url

            r = fmapy.do_search(term)

            mock_get.assert_called_once_with(url)
            mock_url.assert_called_once_with(term)
            self.assertIsInstance(r, unittest.mock.Mock)


if __name__ == "__main__":
    unittest.main()
