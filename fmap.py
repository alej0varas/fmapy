import logging
import pathlib
import urllib


import browsers
import caches


class Fmapy:
    def __init__(self):
        fmapy_path = pathlib.Path.home().joinpath(".fmapy")
        fmapy_path.mkdir(exist_ok=True)
        cache_path = str(fmapy_path.joinpath("cache.txt"))
        download_path = fmapy_path.joinpath("downloads")
        try:
            open(cache_path, "x")
        except FileExistsError:
            pass

        self.browser = browsers.FMASearch()
        self._cache = caches.Cache(cache_path)
        self._download_path = download_path

    def download_song(self, song):
        if song in self._cache:
            return
        url_full = self.browser.get_full_url(song)
        filename = self._get_filename_for_song(url_full)
        content = self.browser.download_song(url_full)
        if content:
            self._write_song_to_file(filename, content)
            self._cache.write(song)
        else:
            logging.error("Failed to download " + song)
            raise FmapyError
        return filename

    def _write_song_to_file(self, filename, content):
        with open(filename, "wb") as song_file:
            song_file.write(content)

    def _get_filename_for_song(self, url):
        path_from_url = urllib.parse.urlparse(url).path
        cut = "/music/"
        path = self._download_path.joinpath(
            pathlib.Path(path_from_url[path_from_url.find(cut) + len(cut) :])
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class FmapyError(Exception):
    pass


def main(UI_class):
    UI_class(Fmapy())


if __name__ == "__main__":
    import uis

    main(uis.CUISearch)
