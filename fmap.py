import pathlib
import random
import re
import time
import urllib

from bs4 import BeautifulSoup
import requests


TIMEOUT = 30
URL = "https://freemusicarchive.org/search/?quicksearch="
RESULTS_STRING = "Search Results:"


class Browser:
    def __iter__(self):
        return self

    def __next__(self):
        song = self._get_next_song()
        if song:
            return song
        raise StopIteration

    def _get_next_song(self):
        if not hasattr(self, "_items"):
            self._items = []
            self._get_songs()
        try:
            song = self._items.pop()
        except IndexError:
            self._get_next_page()
            self._get_songs()
            return self._get_next_song()
        return song

    def _get_songs(self):
        for item in self._soup.find_all(attrs={"class": "js-download"}):
            url = item.attrs["data-url"][: -len("overlay")]
            self._items.append(url)
        random.shuffle(self._items)

    def _get_next_page(self):
        self._url = (
            self._soup.find_all(text=re.compile("NEXT"))[0]
            .parents.__next__()
            .attrs["href"]
        )
        self._get_page()

    def _get_page(self):
        response = requests.get(self._url, timeout=TIMEOUT)
        if response.status_code == 200:
            self._content = response.content
        self._get_soup()

    def _get_soup(self):
        self._soup = BeautifulSoup(self._content, "html.parser")


class Cache:
    def __init__(self, path, items):
        self._path = path
        self._items = items

    def __contains__(self, item):
        return item in self._items

    def write(self, item):
        with open(self._path, "a") as cache_file:
            cache_file.write(item + "\n")


class Fmapy:
    def __init__(self):
        self.downloaded_count = 0

        fmapy_path = pathlib.Path.home().joinpath(".fmapy")
        fmapy_path.mkdir(exist_ok=True)
        cache_path = fmapy_path.joinpath("cache.txt")
        download_path = fmapy_path.joinpath("downloads")
        try:
            open(cache_path, "x")
        except FileExistsError:
            pass
        with open(cache_path) as cache_file:
            cache = Cache(cache_path, map(str.strip, cache_file.readlines()))
        self._cache = cache
        self._download_path = download_path

    def download_song(self, song):
        filename = None
        if song in self._cache:
            return filename

        response = requests.get(song)
        if response.status_code == 200:
            filename = self._write_song_to_file(response.url, response.content)
            self._cache.write(song)
            self.downloaded_count += 1

        nap = random.randint(30, 60)
        time.sleep(nap)

        return filename

    def _write_song_to_file(self, url, content):
        filename = self._get_filename_for_song(url)
        with open(filename, "wb") as song_file:
            song_file.write(content)
        return filename

    def _get_filename_for_song(self, url):
        _path = urllib.parse.urlparse(url).path
        _cut = "/music/"
        path = self._download_path.joinpath(
            pathlib.Path(_path[_path.find(_cut) + len(_cut) :])
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class BrowserSearch(Browser):
    def search(self, search_term):
        self._search_term = search_term
        self._do_search()
        return self._soup.find(id="page-header").text

    def _do_search(self):
        self._url = URL + self._search_term
        self._get_page()


class UISearch:
    def __init__(self, fmapy):
        self._fmapy = fmapy
        self.main()

    def main(self):
        searching = True
        browser = BrowserSearch()
        while searching:
            search_term = input("What are you looking for: ")
            print(browser.search(search_term))
            answer = input("Do you want to download them [Y/n]")
            if answer.lower() in ["y", ""]:
                searching = False

        for song in browser:
            print("Downloading: ", song)
            filename = self._fmapy.download_song(song)
            if filename:
                print("Ready at: ", filename)
            else:
                print("Song in cache")
        print("Downloaded: ", self._fmapy.downloaded_count, " songs")


def main(UI_class):
    UI_class(Fmapy())


if __name__ == "__main__":
    main(UISearch)
