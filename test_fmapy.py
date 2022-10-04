import unittest
import unittest.mock


import fmap
import uis


URL_404 = "https://freemusicarchive.org/track/OX/download"


class FmapyTests(unittest.TestCase):
    def test_download_song_exception(self):
        f = fmap.Fmapy()
        with unittest.mock.patch.object(
            f.browser, "download_song", return_value=None
        ), unittest.mock.patch.object(f.browser, "get_full_url", return_value=""):
            self.assertRaises(fmap.FmapyError, f.download_song, URL_404)


class CLISearchTests(unittest.TestCase):
    def test_main_fmapyerro_exception(self):
        f = fmap.Fmapy()
        u = uis.CLISearch(f)
        with unittest.mock.patch(
            "browsers.FMABrowser.__next__", side_effect=(URL_404, StopIteration)
        ), unittest.mock.patch.object(
            f, "download_song", side_effect=fmap.FmapyError
        ), unittest.mock.patch.object(
            uis.CLISearch, "search"
        ):
            u.main()


if __name__ == "__main__":
    unittest.main()
