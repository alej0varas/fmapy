import requests


BASE_URL = "https://freemusicarchive.org/"
SEARCH_URL = BASE_URL + "search/?quicksearch="


def get_search_base_url():
    return SEARCH_URL


def get_search_url(term):
    return get_search_base_url() + "+".join(term.split())


def do_search(term):
    url = get_search_url(term)
    r = requests.get(url)
    return r
