from .context import fmapy

import unittest
import unittest.mock

from bs4 import Tag

from . import examples


TRACK_INFO_KEYS = [
    "id",
    "handle",
    "url",
    "title",
    "artistName",
    "artistUrl",
    "playbackUrl",
    "downloadUrl",
]


class TrackTests(unittest.TestCase):
    @unittest.mock.patch.object(fmapy.Track, "_get_track_info")
    def test_construct(self, mock_info):

        track = fmapy.Track(examples.TRACK_SOUP)

        self.assertTrue(hasattr(track, "_soup"))
        self.assertIsInstance(track._soup, Tag)
        self.assertTrue(hasattr(track, "_info"))
        mock_info.assert_called_once_with()

    def test_get_track_info(self):
        info = fmapy.Track(examples.TRACK_SOUP)._get_track_info()

        self.assertIsInstance(info, dict)
        self.assertListEqual(TRACK_INFO_KEYS, list(info))

    def test_get_track_title(self):
        title = fmapy.Track(examples.TRACK_SOUP).get_track_title()
        self.assertEqual(title, "De Cuba")

    def test_get_track_duration(self):
        duration = fmapy.Track(examples.TRACK_SOUP).get_track_duration()
        self.assertEqual("03:53", duration)

    def test_get_track_artist(self):
        artist = fmapy.Track(examples.TRACK_SOUP).get_artist()
        self.assertEqual("SONGO 21", artist)

    def test_get_album(self):
        album = fmapy.Track(examples.TRACK_SOUP).get_album()
        self.assertEqual("SONGO 21 - Studio sessions 2003", album)

    def test_get_genres(self):
        genres = fmapy.Track(examples.TRACK_SOUP).get_genres()
        self.assertEqual("Salsa", genres)

        _genres = [
            "International",
            "Novelty",
            "Latin America",
            "Latin",
            "Salsa",
            "Instrumental",
        ]
        genres = fmapy.Track(examples.TRACK_SOUP_1).get_genres()
        self.assertEqual(genres, _genres)

    def test_get_url(self):
        url = fmapy.Track(examples.TRACK_SOUP).get_url()
        self.assertEqual(
            url,
            "https://freemusicarchive.org/music/SONGO_21/SONGO_21_-_Studio_sessions_2003/05_-_De_Cuba/",
        )
