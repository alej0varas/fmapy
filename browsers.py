import random

import requests
from bs4 import BeautifulSoup


class FMABrowser:
    URL = "https://freemusicarchive.org/search/?quicksearch="
    TIMEOUT = 30

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
        response = requests.get(self._url, timeout=self.TIMEOUT)
        if response.status_code == 200:
            self._content = response.content
        self._get_soup()

    def _get_soup(self):
        self._soup = BeautifulSoup(self._content, "html.parser")


class FMASearch(FMABrowser):
    def search(self, search_term):
        self._search_term = search_term
        self._do_search()
        return self._soup.find(id="page-header").text

    def _do_search(self):
        self._url = self.URL + self._search_term
        self._get_page()
