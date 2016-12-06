import os
import requests
import requests_cache
import tempfile
import threading

import pygame


FMA_API_URL = 'https://freemusicarchive.org/api/get/{0}.{1}?api_key={2}'
FMA_API_KEY = os.environ.get('FMA_API_KEY')
FMA_API_FORMAT = os.environ.get('FMA_API_FORMAT', 'json')
FMA_API_DATASETS = ['artists', 'albums', 'tracks', 'genres', 'curators']
FMA_API_ITEMS_LIMIT = 50
FMA_TRACK_SINGLE_URL = 'http://freemusicarchive.org/services/track/single/{0}.' + FMA_API_FORMAT


def get_project_dir(subdir=''):
    project_dir = os.path.expanduser(os.path.join('~', '.fmap', subdir))
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    return project_dir


requests_cache.install_cache(
    os.path.join(get_project_dir('cache'),
    'requests_cache')
    ) # :)


class Browser:

    _genres = None
    track = None
    tracks = None
    page = None

    @property
    def genres(self):
        if not self._genres:
            self._load_genres()
        return self._genres

    def get_next_track(self):
        if self.tracks is None:
            self.load_tracks()
        if self.page > self.total_pages:
            return False
        try:
            self.track = self.tracks.pop()
        except IndexError:
            self.page += 1
            self.tracks = None
            return self.get_next_track()
        return True

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
        print(response.url, ['not', 'in'][response.from_cache], 'cache')

        if response.ok:
            return response

    def _get_content_as_json(self, url):  # as_format?
        content = self._get_content(url).json()
        return content

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
        if self.page is not None:
            url += '&page=' + str(self.page)
        url += '&limit=' + str(FMA_API_ITEMS_LIMIT)
        data = self._get_content_as_json(url)
        self.page = data['page']
        self.total_pages = data['total_pages']
        return data['dataset']


class Player:

    track = None
    next_track = None
    next_track_file = None
    t = None
    pause = True

    def __init__(self):
        self.q = False
        self.b = Browser()
        for index, genre in enumerate(self.b.genres):
            print(index, genre['genre_title'])
        option = int(input('Choose a genre: '))
        self.b.set_genre(option)

        pygame.init()
        self.m = pygame.mixer.music
        self.t_stop = threading.Event()

        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

    def run(self):
        option = 'p'
        while not self.q:
            if option == 'q':
                self.stop()
                continue
            if option == 'n':
                self.next()
            if option == 'p':
                self.pause()
            if option == 'i':
                self.info()
            option = input('>> ')

    def next(self):
        self.m.stop()
        self.play()

    def pause(self):
        if not self.track:
            self.play()
            return
        if self.is_paused:
            self.is_paused = False
            self.m.unpause()
        else:
            self.is_paused = True
            self.m.pause()

    def play(self):
        if self.next_track is not None:
            self.track = self.next_track
            self.track_file = self.next_track_file
        if self.track is None:
            self.b.get_next_track()
            self.track = self.b.track
            self.track_file = self.get_song_cache_file_name()

        try:
            self.m.load(self.track_file)
            self.m.play()
            self.is_paused = False
            self.info()
        except Exception as e:
            print(e)
            self.track = None
            self.play()
            return

        if not self.b.get_next_track():
            print('the end')
            self.stop()
        self.next_track = self.b.track
        self.next_track_file = self.get_song_cache_file_name()

        self._play_thread()

    def info(self):
        print(self.track['track_title'], '|',
              self.track['artist_name'], '|',
              self.track['album_title'], '(',
              self.track['track_duration'], ')<',
              self.track['track_id'], '>',
        )

    def get_song_cache_file_name(self):
        project_dir = get_project_dir('cache')
        tmp_track_file_name = os.path.join(project_dir, str(self.b.track['track_id'])) + '.mp3'
        in_cache = True
        if not os.path.exists(tmp_track_file_name):
            in_cache = False
            with open(tmp_track_file_name, 'wb') as tmp_track:
                track = self.b._get_content(self.b._get_track_url())
                tmp_track.write(track.content)
        print(tmp_track_file_name, ['not', 'in'][in_cache], 'cache')
        return tmp_track_file_name

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
                    for event in pygame.event.get():
                        if event.type == self.p.SONG_END:
                            self.p.play()
                    self.q.wait(.5)

        if self.t is not None:
            return

        self.t = PlayThread(kwargs={'p': self, 'q': self.t_stop})
        self.t.start()


if __name__ == '__main__':
    p = Player()
    p.run()
