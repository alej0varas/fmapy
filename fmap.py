import os
import random
import requests
import requests_cache
import threading

import pygame


FMA_API_URL = 'https://freemusicarchive.org/api/get/{0}.{1}?api_key={2}'
FMA_API_KEY = os.environ.get('FMA_API_KEY')
FMA_API_FORMAT = os.environ.get('FMA_API_FORMAT', 'json')
FMA_API_DATASETS = ['artists', 'albums', 'tracks', 'genres', 'curators']
FMA_API_ITEMS_LIMIT = 50
FMA_TRACK_SINGLE_URL = ('https://freemusicarchive.org/services/track/single/'
                        '{0}.' + FMA_API_FORMAT)

assert FMA_API_KEY, ("You need to provide your FMA KEY as an environment "
                     "variable('FMA_API_KEY')")


def get_project_dir(subdir=''):
    project_dir = os.path.expanduser(os.path.join('~', '.fmap', subdir))
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    return project_dir


def get_dataset_item_class(dataset_name):
    class_name = dataset_name[:-1].capitalize()
    return globals()[class_name]


class Content:

    def get_content(self, url, json=True):
        response = requests.get(url)
        print(response.url, ['not', 'in'][response.from_cache], 'cache')

        if response.ok:
            if json:
                return response.json()
            else:
                return response.content


class Genre:

    pass


class Track(Content):

    def get_url(self):
        content = self.get_content(FMA_TRACK_SINGLE_URL.format(self.track_id))
        return content['track_listen_url']


class BaseBrowser(Content):

    def __init__(self, use_cache=True):
        self.items = []
        self.base_url = FMA_API_URL.format(
            self.dataset_name, FMA_API_FORMAT, FMA_API_KEY
        )
        self.dataset_class = get_dataset_item_class(self.dataset_name)

        if use_cache:
            requests_cache.install_cache(
                os.path.join(get_project_dir('cache'), 'requests_cache')
            )

    def load_dataset_all(self):
        [i for i in self._load_dataset_all()]

    def load_dataset_by_page(self):
        return self._load_dataset_all()

    def get_url(self):
        return self.base_url

    def reset_items(self):
        self.items = []

    def _load_dataset_all(self):
        page = None
        while True:
            dataset, page = self._load_dataset_page(page)
            if dataset is None:
                break
            self._set_items(dataset)
            page = str(int(page) + 1)
            yield

    def _load_dataset_page(self, page=None):
        url = self.get_url()
        if page is not None:
            url += '&page=' + page
        url += '&limit=' + str(FMA_API_ITEMS_LIMIT)

        data = self.get_content(url)

        if page is not None and int(data['page']) < int(page):
            return None, None
        return data['dataset'], data['page']

    def _set_items(self, dataset):
        for item in dataset:
            i = self.dataset_class()
            i.__dict__.update(item)
            self.items.append(i)


class GenresBrowser(BaseBrowser):

    dataset_name = 'genres'

    def __init__(self):
        super(GenresBrowser, self).__init__()
        self.load_dataset_all()


class TrackBrowser(BaseBrowser):

    dataset_name = 'tracks'
    page = 0
    pager = None
    genre = None

    def __init__(self):
        super(TrackBrowser, self).__init__()

    def get_url(self):
        url = self.base_url
        if self.genre:
            url += '&genre_id=' + self.genre.genre_id
        return url

    def load_next_page(self):
        if getattr(self, 'pager') is None:
            self.pager = self.load_dataset_by_page()
        self.pager.__next__()

    def set_genre(self, genre):
        self.reset_items()
        self.pager = None
        self.genre = genre


class PlayList:

    def __init__(self, track_browser):
        self.track_browser = track_browser
        self.reset()

    def set_tracks(self, tracks):
        self.tracks = tracks

    def get_next_track(self):
        self.current_track_index += 1
        return self.get_current_track()

    def get_current_track(self):
        return self.get_track(self.current_track_index)

    def get_track(self, index):
        try:
            track = self.tracks[index]
            return track
        except IndexError as e:
            result = self.load_tracks()
            if result:
                track = self.get_track(index)
                return track
            raise e

    def load_tracks(self):
        try:
            self.track_browser.load_next_page()
            self.set_tracks(self.track_browser.items)
            return True
        except StopIteration:
            return False

    def reset(self, load=False):
        self.tracks = []
        self.current_track_index = 0
        if load:
            self.load_tracks()


class Player:

    track = None
    _play = None
    _pause = None
    _next = None
    _stop = None
    is_playing = False
    _settings = {
        'only_new': False,
        'only_instrumental': False
    }

    def __init__(self, track_ended_callback, play_failed_callback, is_playable_callback):
        self.track_browser = TrackBrowser()
        self.genres_browser = GenresBrowser()
        self.play_list = PlayList(self.track_browser)

        self.track_ended_callback = track_ended_callback
        self.play_failed_callback = play_failed_callback
        self.is_playable_callback = is_playable_callback
        pygame.init()
        self.mixer = pygame.mixer.music
        self.t_stop = threading.Event()

        self.TRACK_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.TRACK_END)

        self._start_auto_play()

    def pause(self):
        self._pause = True

    def do_pause(self):
        if self.is_playing:
            self.is_playing = False
            self.mixer.pause()
        else:
            self.is_playing = True
            self.mixer.unpause()

    def play(self, track):
        self.track = track
        self._play = True

    def do_play(self):
        if not self.is_playable_callback(self.track):
            self.next()
        try:
            self.mixer.load(self.get_track_file_name(self.track))
            self.mixer.play()
            self.is_playing = True
        except pygame.error as e:
            print(e)
            self.play_failed_callback()

    def next(self):
        self._next = True

    def do_next(self):
        self.mixer.stop()
        self.is_playing = False
        self.play_next_track()

    def stop(self):
        self._stop = True

    def do_stop(self):
        self.mixer.stop()
        self.t_stop.set()

    def enumerate_genres(self, genres):
        genres.sort(key=lambda x: x.genre_title)
        enumerated = list(enumerate(genres))
        return enumerated

    def get_current_track(self):
        return self.play_list.get_current_track()

    def _get_track_file_name(self, track):
        project_dir = get_project_dir('cache')
        tmp_track_file_name = os.path.join(
            project_dir, str(track.track_id)
        ) + '.mp3'
        return tmp_track_file_name

    def get_track_file_name(self, track):
        in_cache = True
        tmp_track_file_name = self._get_track_file_name(track)
        if not os.path.exists(tmp_track_file_name):
            in_cache = False
            with open(tmp_track_file_name, 'wb') as tmp_track:
                track = track.get_content(track.get_url(), json=False)
                tmp_track.write(track)
        print(tmp_track_file_name, ['not', ''][in_cache], 'in cache')
        return tmp_track_file_name

    def get_parent_genres(self):
        genres = [g for g in self.genres_browser.items if not g.genre_parent_id]
        return genres

    def get_settings(self):
        return self._settings

    def load_random_genre(self):
        self.set_genre(random.choice(self.genres_browser.items))

    def search_genres(self, term):
        genres = []
        for g in self.genres_browser.items:
            if term.lower() in g.genre_title.lower():
                genres.append(g)
        return genres

    def play_random_genre(self):
        self.load_random_genre()
        self.play_current_track()

    def is_busy(self):
        return self.mixer.get_busy()

    def play_current_track(self):
        track = self.play_list.get_current_track()
        self.play(track)

    def play_next_track(self):
        track = self.play_list.get_next_track()
        self.play(track)

    def set_genre(self, genre):
        self.track_browser.set_genre(genre)
        self.play_list.reset(load=False)

    def settings(self, **kwargs):
        self._settings.update(**kwargs)

    def _start_auto_play(self):
        self._auto_play_thread = AutoPlayThread(kwargs={'player': self})
        self._auto_play_thread.start()


class AutoPlayThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        self.player = kwargs['kwargs']['player']
        super(AutoPlayThread, self).__init__(*args, **kwargs)

    def run(self):
        while not self.player.t_stop.is_set():
            for event in pygame.event.get():
                if event.type == self.player.TRACK_END:
                    self.player.next()
            if self.player._pause:
                self.player._pause = False
                self.player.do_pause()
            if self.player._play:
                self.player._play = False
                self.player.do_play()
            if self.player._next:
                self.player._next = False
                self.player.do_next()
            if self.player._stop:
                self.player._stop = False
                self.player.do_stop()

            self.player.t_stop.wait(.1)

