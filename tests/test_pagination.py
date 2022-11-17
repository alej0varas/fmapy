from .context import fmapy

import unittest
import unittest.mock

from . import examples


class PaginationTests(unittest.TestCase):
    pagination = fmapy.Pagination(examples.PAGE_SOUP)

    def test_construct(self):
        pagination = fmapy.Pagination(examples.PAGE_SOUP)

        self.assertTrue(hasattr(pagination, "_soup"))
        self.assertEqual(examples.PAGE_SOUP, pagination._soup)

    def test_get_items_info(self):
        info_expected = {
            "from": "1",
            "to": "20",
            "of": "43",
            "selected": "20",
            "options": ["15", "20", "25", "50", "100", "200"],
        }

        pagination = PaginationTests.pagination.get_items_info()

        self.assertDictEqual(info_expected, pagination)
