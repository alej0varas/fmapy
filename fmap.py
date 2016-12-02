import os
import requests
import requests_cache

requests_cache.install_cache()  # :)


FMA_API_URL = 'https://freemusicarchive.org/api/get/{0}.{1}?api_key={2}'
FMA_API_KEY = os.environ.get('FMA_API_KEY')
FMA_API_FORMAT = os.environ.get('FMA_API_FORMAT', 'json')
FMA_API_DATASETS = ['artists', 'albums', 'tracks', 'genres', 'curators']
FMA_TRACK_SINGLE_URL = 'http://freemusicarchive.org/services/track/single/{0}.' + FMA_API_FORMAT


class Browser:

    _genres = None
    track = None
    tracks = None

    @property
    def genres(self):
        if not self._genres:
            self._load_genres()
        return self._genres

    def get_next_track(self):
        if self.tracks is None:
            self.load_tracks()
        try:
            self.track = self._get_track_url(self.tracks.pop())
            return True
        except IndexError:
            return False

    def _load_genres(self):
        self._genres = self._get_dataset('genres')

    def load_tracks(self):
        self.tracks = self._get_tracks()

    def set_genre(self, option):
        self.genre = self.genres[option]

    def _build_url(self, dataset):
        url = FMA_API_URL.format(dataset, FMA_API_FORMAT, FMA_API_KEY)
        return url

    def _get_content(self, url):
        response = requests.get(url)
        print(response.url)
        print(response.from_cache)
        if  response.ok:
            return response.json()  # will fail for other formats

    def _get_dataset(self, name):
        assert name in FMA_API_DATASETS
        url = self._build_url(name)
        data = self._get_content(url)
        return data['dataset']

    def _get_track_url(self, track):
        id = track['track_id']
        content = self._get_content(FMA_TRACK_SINGLE_URL.format(id))
        return content['track_listen_url']

    def _get_tracks(self):
        url = self._build_url('tracks')
        if self.genre:
            url += '&genre_id=' + self.genre['genre_id']
        data = self._get_content(url)
        return data['dataset']


def play(url):
    import subprocess
    subprocess.Popen(['mpv', '--no-video', '--no-terminal', url]).wait()

    
if __name__ == '__main__':
    b = Browser()
    for index, genre in enumerate(b.genres):
        print(index, genre['genre_title'])
    option = int(input('Choose a genre: '))
    b.set_genre(option)
    while b.get_next_track():
        play(b.track)
