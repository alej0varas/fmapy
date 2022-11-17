from json import loads

from bs4 import BeautifulSoup

import requests


BASE_URL = "https://freemusicarchive.org/"
SEARCH_URL = BASE_URL + "search/?quicksearch="


def get_page_items(html):
    items = BeautifulSoup(html, "html.parser").find_all("div", "play-item")
    return items


def get_page_pagination(html):
    return Pagination(html)


def get_search_base_url():
    return SEARCH_URL


def get_search_url(term):
    return get_search_base_url() + "+".join(term.split())


def do_search(term):
    url = get_search_url(term)
    response = requests.get(url)
    return response.content


class Pagination:
    def __init__(self, soup):
        self._soup = soup

    def get_items_info(self):
        pagination = self._soup.findChild("div", "pagination-full")
        selected = pagination.findChildren("option", selected=True)[0].attrs["value"]
        from_to_of = [
            i.text for i in pagination.findChildren("span")[0].findChildren("b")
        ]
        options = [i.attrs["value"] for i in pagination.findChildren("option")]
        pagination = {
            "from": from_to_of[0],
            "to": from_to_of[1],
            "of": from_to_of[2],
            "options": options,
            "selected": selected,
        }

        return pagination


class Track:
    def __init__(self, soup):
        self._soup = soup
        self._info = self._get_track_info()

    def _get_track_info(self):
        return loads(self._soup["data-track-info"])

    def get_album(self):
        return self._soup.findChild("span", "ptxt-album").text.strip()

    def get_artist(self):
        return self._info["artistName"]

    def get_genres(self):
        genres = self._soup.findChild("span", "ptxt-genre").text.split(",")
        genres = [g.strip() for g in genres]
        if len(genres) == 1:
            genres = genres[0]
        return genres

    def get_track_title(self):
        return self._info["title"]

    def get_track_duration(self):
        return self._soup.findChildren("span", recursive=False)[4].text.strip()

    def get_url(self):
        return self._info["url"]
