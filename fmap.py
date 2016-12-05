import os
import requests
import requests_cache
import tempfile
import threading

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
            self.track = self.tracks.pop()
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
        if response.ok:
            return response

    def _get_content_as_json(self, url):  # as_format?
        return self._get_content(url).json()

    def _get_dataset(self, name):
        assert name in FMA_API_DATASETS
        url = self._build_url(name)
        data = self._get_content_as_json(url)
        return data['dataset']

    def _get_track_url(self):
        content = self._get_content_as_json(FMA_TRACK_SINGLE_URL.format(self.track['track_id']))
        return content['track_listen_url']

    def _get_tracks(self):
        url = self._build_url('tracks')
        if self.genre:
            url += '&genre_id=' + self.genre['genre_id']
        data = self._get_content_as_json(url)
        return data['dataset']


class Player:

    t = None

    def __init__(self):
        self.q = False
        self.b = Browser()
        for index, genre in enumerate(self.b.genres):
            print(index, genre['genre_title'])
        option = int(input('Choose a genre: '))
        self.b.set_genre(option)

        import pygame
        pygame.mixer.init()
        self.m = pygame.mixer.music
        self.t_stop = threading.Event()

    def run(self):
        option = 'p'
        while not self.q:
            if option == 'q':
                self.stop()
                continue
            if option == 'n':
                option = 'p'
            if option == 'p':
                self.play()
            option = input('>> ')

    def play(self):
        self.b.get_next_track()
        track = self.b._get_content(self.b._get_track_url())
        tmp_track = tempfile.NamedTemporaryFile()
        tmp_track.write(track.content)
        print(self.b.track['track_title'], '|',
              self.b.track['artist_name'], '|',
              self.b.track['album_title'])
        self.m.load(tmp_track.name)
        self.m.play()
        if self.t is None:
            self._play_thread()

    def stop(self):
        self.m.stop()
        self.t_stop.set()
        self.q = True

    def _play_thread(self):

        class PlayThread(threading.Thread):
            def __init__(self, *args, **kwargs):
                self.p = kwargs['kwargs']['p']
                self.q = kwargs['kwargs']['q']
                super(PlayThread, self).__init__(*args, **kwargs)

            def run(self):
                while not self.q.is_set():
                    if not self.p.m.get_busy():
                        self.p.play()
                    self.q.wait(.5)

        self.t = PlayThread(kwargs={'p': self, 'q': self.t_stop})
        self.t.start()


if __name__ == '__main__':
    p = Player()
    p.run()
