import random
import time


from bs4 import BeautifulSoup
import requests


class Scraper:
    def __init__(self, nap_min=30, nap_max=60):
        self.nap_min = nap_min
        self.nap_max = nap_max

    def download_song(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            nap = random.randint(self.nap_min, self.nap_max)
            time.sleep(nap)
            return response.content

    def get_full_url(self, url):
        response = requests.get(url, allow_redirects=False)
        return response.next.url
