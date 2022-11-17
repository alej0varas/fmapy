from .context import fmapy

import unittest
import unittest.mock

from . import examples


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
    @unittest.mock.patch("fmapy.core.get_search_url")
    def test_do_search(self, mock_gsu, mock_get):
        term = "mock song"
        url = mock_gsu.return_value = "http://mock.mock/?s=" + term
        response_expected = "<html>response</html>"

        request_mock = unittest.mock.Mock(content=response_expected)
        mock_get.return_value = request_mock
        mock_gsu.return_value = url

        response = fmapy.do_search(term)

        mock_get.assert_called_once_with(url)
        mock_gsu.assert_called_once_with(term)
        self.assertEqual(response_expected, response)

    def test_get_page_items(self):
        items = fmapy.get_page_items(examples.SEARCH_RESULT)
        item_expected = items[0]

        self.assertEqual(len(items), 20)
        self.assertEqual(item_expected, items[0])

    def test_get_page_pagination(self):
        pagination = fmapy.get_page_pagination("")

        self.assertIsInstance(pagination, fmapy.Pagination)
