import logging
import os
import random
import requests
import requests_cache
import threading

import pygame

pygame.init()

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


logging.basicConfig(filename=os.path.join(get_project_dir('log'), 'fmap.log'), filemode='w', level=logging.DEBUG)


class Content:

    def get_content(self, url, json=True):
        response = requests.get(url)
        logging.debug('Content.get_content ' + response.url + [' not', ''][response.from_cache] + ' in cache')

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
        logging.debug('Track.get_url ' + content['track_id'] + ' ' + content['track_url'])
        return content['track_listen_url']


class BaseBrowser(Content):

    total_pages = None
    total = None

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
        logging.debug('BaseBrowser.load_dataset_all')
        [i for i in self._load_dataset_all()]

    def load_dataset_by_page(self):
        logging.debug('BaseBrowser.load_dataset_by_page')
        return self._load_dataset_all()

    def get_url(self):
        logging.debug('BaseBrowser.get_url')
        return self.base_url

    def reset_items(self):
        logging.debug('BaseBrowser.reset_items')
        self.items = []

    def check_totals(self, data):
        logging.debug('BaseBrowser.check_totals')
        self.total_pages = data.get('total_pages', None)
        self.tolal = data.get('total_pages', None)

    def _load_dataset_all(self):
        logging.debug('BaseBrowser._load_dataset_all')
        page = None
        while True:
            dataset, page = self._load_dataset_page(page)
            if dataset is None:
                break
            self._set_items(dataset)
            page += 1
            yield

    def _load_dataset_page(self, page=None):
        logging.debug('BaseBrowser._load_dataset_page')
        if self.total_pages is not None and page is not None and self.total_pages < page:
            return None, None
        url = self.get_url()
        if page is not None:
            url += '&page=' + str(page)
        url += '&limit=' + str(FMA_API_ITEMS_LIMIT)

        data = self.get_content(url)

        self.check_totals(data)

        if page is not None and int(data['page']) < page:
            return None, None
        return data['dataset'], int(data['page'])

    def _set_items(self, dataset):
        logging.debug('BaseBrowser._set_items')
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
        logging.debug('TrackBrowser.get_url')
        url = self.base_url
        if self.genre:
            url += '&genre_id=' + self.genre.genre_id
        return url

    def load_next_page(self):
        logging.debug('TrackBrowser.load_next_page')
        if getattr(self, 'pager') is None:
            self.pager = self.load_dataset_by_page()
        self.pager.__next__()

    def set_genre(self, genre):
        logging.debug('TrackBrowser.set_genre')
        self.reset_items()
        self.pager = None
        self.genre = genre


class PlayList:

    def __init__(self, track_browser):
        self.track_browser = track_browser
        self.reset()

    def set_tracks(self, tracks):
        logging.debug('PlayList.set_tracks')
        self.tracks = tracks

    def get_next_track(self):
        logging.debug('PlayList.get_next_track')
        self.current_track_index += 1
        return self.get_current_track()

    def get_current_track(self):
        logging.debug('PlayList.get_current_track')
        return self.get_track(self.current_track_index)

    def get_track(self, index):
        logging.debug('PlayList.get_track')
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
        logging.debug('PlayList.load_tracks')
        try:
            self.track_browser.load_next_page()
            self.set_tracks(self.track_browser.items)
            return True
        except StopIteration:
            return False

    def reset(self, load=False):
        logging.debug('PlayList.reset')
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
        self.mixer = pygame.mixer.music
        self.t_stop = threading.Event()

        self.TRACK_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.TRACK_END)

        self._start_auto_play()

    def pause(self):
        logging.debug('Player.pause')
        self._pause = True

    def do_pause(self):
        logging.debug('Player.do_pause')
        if self.is_playing:
            self.is_playing = False
            self.mixer.pause()
        else:
            self.is_playing = True
            self.mixer.unpause()

    def play(self, track):
        logging.debug('Player.play')
        self.track = track
        self._play = True
        self.do_play()

    def do_play(self):
        logging.debug('Player.do_play')
        if self.is_playing:
            return
        if not self.is_playable_callback(self.track):
            self.next()
        try:
            self.mixer.load(self.get_track_file_name(self.track))
            self.mixer.play()
            self.is_playing = True
        except pygame.error as e:
            logging.error(e)
            self.play_failed_callback()

    def next(self):
        logging.debug('Player.next')
        self._next = True
        self.do_next()

    def do_next(self):
        logging.debug('Player.do_next')
        self.mixer.stop()
        self.is_playing = False
        self.play_next_track()

    def stop(self):
        logging.debug('Player.stop')
        self._stop = True
        self.do_stop()

    def do_stop(self):
        logging.debug('Player.do_stop')
        self.mixer.stop()
        self.t_stop.set()

    def enumerate_genres(self, genres):
        logging.debug('Player.enumerate_genres')
        genres.sort(key=lambda x: x.genre_title)
        enumerated = list(enumerate(genres))
        return enumerated

    def get_current_track(self):
        logging.debug('Player.get_current_track')
        return self.play_list.get_current_track()

    def _get_track_file_name(self, track):
        logging.debug('Player._get_track_file_name')
        project_dir = get_project_dir('cache')
        tmp_track_file_name = os.path.join(
            project_dir, str(track.track_id)
        ) + '.mp3'
        return tmp_track_file_name

    def get_track_file_name(self, track):
        logging.debug('Player.get_track_file_name')
        in_cache = True
        tmp_track_file_name = self._get_track_file_name(track)
        if not os.path.exists(tmp_track_file_name):
            in_cache = False
            with open(tmp_track_file_name, 'wb') as tmp_track:
                track = track.get_content(track.get_url(), json=False)
                tmp_track.write(track)
        logging.debug('Player.get_track_file_name ' + tmp_track_file_name + [' not', ''][in_cache] + ' in cache')
        return tmp_track_file_name

    def get_parent_genres(self):
        logging.debug('Player.get_parent_genres')
        genres = [g for g in self.genres_browser.items if not g.genre_parent_id]
        return genres

    def get_settings(self):
        logging.debug('Player.get_settings')
        return self._settings

    def load_random_genre(self):
        logging.debug('Player.load_random_genre')
        self.set_genre(random.choice(self.genres_browser.items))

    def search_genres(self, term):
        logging.debug('Player.search_genres')
        genres = []
        for g in self.genres_browser.items:
            if term.lower() in g.genre_title.lower():
                genres.append(g)
        return genres

    def play_random_genre(self):
        logging.debug('Player.play_random_genre')
        self.load_random_genre()
        self.play_current_track()

    def is_busy(self):
        logging.debug('Player.is_busy')
        return self.mixer.get_busy()

    def play_current_track(self):
        logging.debug('Player.player_current_track')
        track = self.play_list.get_current_track()
        self.play(track)

    def play_next_track(self):
        logging.debug('Player.play_next_track')
        track = self.play_list.get_next_track()
        self.play(track)

    def set_genre(self, genre):
        logging.debug('Player.set_genre')
        self.track_browser.set_genre(genre)
        self.play_list.reset(load=False)

    def settings(self, **kwargs):
        logging.debug('Player.settings')
        self._settings.update(**kwargs)

    def _start_auto_play(self):
        self._auto_play_thread = AutoPlayThread(kwargs={'player': self})
        self._auto_play_thread.start()

    def get_pos(self):
        pos = self.mixer.get_pos()
        if pos == -1:
            return '00:00'
        seconds = (pos // 1000) % 60
        minutes = (pos // (1000 * 60)) % 60
        hours = (pos // (1000 * 60 * 60)) % 24
        pos_str = str(hours) + ':' + str(minutes) + ':' + str(seconds)
        logging.debug('Player.get_pos ' + pos_str)
        return pos_str

class AutoPlayThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        self.player = kwargs['kwargs']['player']
        super(AutoPlayThread, self).__init__(*args, **kwargs)

    def run(self):
        # First time sleep a little to avoid track end event
        self.player.t_stop.wait(2)
        while not self.player.t_stop.is_set():
            for event in pygame.event.get():
                if event.type == self.player.TRACK_END:
                    logging.debug('AutoPlayThread.run TRACK_END event')
                    self.player.next()
            if self.player._pause:
                logging.debug('AutoPlayThread.run pause')
                self.player._pause = False
                self.player.do_pause()
            if self.player._play:
                logging.debug('AutoPlayThread.run play')
                self.player._play = False
                self.player.do_play()
            if self.player._next:
                logging.debug('AutoPlayThread.run next')
                self.player._next = False
                self.player.do_next()
            if self.player._stop:
                logging.debug('AutoPlayThread.run stop')
                self.player._stop = False
                self.player.do_stop()

            self.player.t_stop.wait(.1)
