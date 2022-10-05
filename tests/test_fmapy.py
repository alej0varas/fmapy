from .context import fmapy

import unittest
import unittest.mock


URL_404 = "https://freemusicarchive.org/track/OX/download"


class FmapyTests(unittest.TestCase):
    def test_download_song_exception(self):
        f = fmapy.Fmapy()
        with unittest.mock.patch.object(
            f.browser, "download_song", return_value=None
        ), unittest.mock.patch.object(f.browser, "get_full_url", return_value=""):
            self.assertRaises(fmapy.exceptions.FmapyError, f.download_song, URL_404)


class CLISearchTests(unittest.TestCase):
    def test_main_fmapyerro_exception(self):
        f = fmapy.Fmapy()
        u = fmapy.uis.CLISearch(f)
        with unittest.mock.patch(
            "fmapy.browsers.FMABrowser.__next__", side_effect=(URL_404, StopIteration)
        ), unittest.mock.patch.object(
            f, "download_song", side_effect=fmapy.exceptions.FmapyError
        ), unittest.mock.patch.object(
            fmapy.uis.CLISearch, "search"
        ):
            u.main()


if __name__ == "__main__":
    unittest.main()
