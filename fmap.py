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


requests_cache.install_cache(
    os.path.join(get_project_dir('cache'), 'requests_cache')
)  # :)


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

    def __init__(self):
        self.items = []
        self.base_url = FMA_API_URL.format(
            self.dataset_name, FMA_API_FORMAT, FMA_API_KEY
        )
        self.dataset_class = get_dataset_item_class(self.dataset_name)

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


class Player:

    is_playing = False
    t = None

    def __init__(self, song_ended_callback, play_failed_callback):
        self.song_ended_callback = song_ended_callback
        self.play_failed_callback = play_failed_callback
        pygame.init()
        self.m = pygame.mixer.music
        self.t_stop = threading.Event()

        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        self._play_thread()

    def pause(self):
        if self.is_playing:
            self.is_playing = False
            self.m.pause()
        else:
            self.is_playing = True
            self.m.unpause()

    def play(self, track_file_name):
        try:
            self.m.load(track_file_name)
            self.m.play()
            self.is_playing = True
        except pygame.error as e:
            print(e)
            self.play_failed_callback()

    def next(self):
        self.m.stop()
        self.play()

    def stop(self):
        self.m.stop()
        self.t_stop.set()

    def is_busy(self):
        return self.m.get_busy()

    def _play_thread(self):

        class PlayThread(threading.Thread):

            def __init__(self, *args, **kwargs):
                self.p = kwargs['kwargs']['p']
                super(PlayThread, self).__init__(*args, **kwargs)

            def run(self):
                while not self.p.t_stop.is_set():
                    for event in pygame.event.get():
                        if event.type == self.p.SONG_END:
                            self.p.song_ended_callback()
                    self.p.t_stop.wait(.5)

        self.t = PlayThread(kwargs={'p': self})
        self.t.start()


class PlayList:

    tracks = []
    current_track_index = 0

    def set_tracks(self, tracks):
        self.tracks = tracks

    def get_track(self):
        try:
            track = self.tracks[self.current_track_index]
            self.current_track_index += 1
            return track
        except IndexError:
            return None


class BaseUI:

    track = None
    _settings = {
        'only_new': False,
        'only_instrumental': False
    }

    def __init__(self):
        self.settings()
        self.q = False

        self.tb = TrackBrowser()
        self.gb = GenresBrowser()
        self.pl = PlayList()
        self.pr = Player(self.song_ended, self.play_failed)

    def append_item_by_category(self, item, category, repeat=False):
        items = self.get_items_by_category(category)
        items.append(item.track_id)
        if not repeat:
            items = set(items)
        self.store_items_by_category(items, category)

    def enumerate_genres(self, genres):
        genres.sort(key=lambda x: x.genre_title)
        enumerated = list(enumerate(genres))
        return enumerated

    def favourite(self):
        self.append_item_by_category(self.track, 'favourites')

    def get_category_file_path(self, category):
        category_file_path = os.path.join(
            get_project_dir(category), category + '.txt'
        )
        return category_file_path

    def get_items_by_category(self, category):
        items_file_path = self.get_category_file_path(category)
        items = []
        try:
            items_file = open(items_file_path, 'r')
            items = [i.strip() for i in items_file.readlines()]
            items_file.close()
        except FileNotFoundError:
            pass
        return items

    def get_parent_genres(self):
        genres = [g for g in self.gb.items if not g.genre_parent_id]
        return genres

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

    def hate(self):
        self.append_item_by_category(self.track, 'hates')

    def is_busy(self):
        return self.pr.is_busy()

    def is_favourite(self, track):
        return self.is_item_in_category(track, 'favourites')

    def is_hated(self, track):
        return self.is_item_in_category(track, 'hates')

    def is_item_in_category(self, item, category):
        items = self.get_items_by_category(category)
        return item.track_id in items

    def load_random_genre(self):
        self.set_genre(random.choice(self.gb.items))

    def search_genres(self, term):
        genres = []
        for g in self.gb.items:
            if term.lower() in g.genre_title.lower():
                genres.append(g)
        return genres

    def song_ended(self):
        self.append_item_by_category(self.track, 'endeds', repeat=True)
        self.play()

    def load_tracks(self):
        try:
            self.tb.load_next_page()
            self.pl.set_tracks(self.tb.items)
            return True
        except StopIteration:
            return False

    def pause(self):
        self.pr.pause()

    def play(self):
        self.track = self.pl.get_track()
        if self.track is None:
            result = self.load_tracks()
            if result:
                self.play()
            return
        if self.is_hated(self.track):
            print('haters gonna hate')
            self.next()
            return
        if self._settings['only_new'] and not self.track_is_new(self.track):
            print('skipping not new')
            self.next()
            return
        if self._settings['only_instrumental'] and not int(self.track.track_instrumental):
            print('skipping not instrumental')
            self.next()
            return

        track_file_name = self.get_track_file_name(self.track)
        self.pr.play(track_file_name)

    def play_failed(self):
        self.append_item_by_category(self.track, 'failed', repeat=True)
        self.play()

    def play_random_genre(self):
        self.load_random_genre()
        self.play()

    def next(self):
        self.append_item_by_category(self.track, 'skipped', repeat=True)
        self.play()

    def set_genre(self, genre):
        self.tb.set_genre(genre)
        self.pl = PlayList()
        self.load_tracks()

    def settings(self, **kwargs):
        self._settings.update(**kwargs)

    def stop(self):
        self.pr.stop()

    def store_items_by_category(self, items, category):
        items_file_path = self.get_category_file_path(category)
        items = '\n'.join(items)
        with open(items_file_path, 'w') as items_file:
            items_file.write(items)

    def track_is_new(self, track):
        tmp_track_file_name = self._get_track_file_name(track)
        return not os.path.exists(tmp_track_file_name)

    def quit(self):
        self.stop()
        self.q = True


class CLI(BaseUI):

    def choose_genre_from_list(self, genres):
        enumerated = self.enumerate_genres(genres)
        for index, genre in enumerated:
            print(index, genre.genre_title)
        while True:
            option = input('Choose a genre: ')
            try:
                option = int(option)
                self.set_genre(enumerated[option][1])
                break
            except (ValueError, IndexError):
                print(':/')
        self.play()

    def menu(self):
        while not self.q:
            self.status()
            option = input('>> ')
            if option == 'g':
                self.play_from_parent_genre()
            if option == 'o':
                self.settings(only_new=not self._settings['only_new'])
            if option == 'r':
                self.play_random_genre()
            if option == 's':
                self.play_genre_from_search()
            if option == 't':
                self.stop()
            if option == 'a':
                self.play()
            if option == 'i':
                self.settings(only_instrumental=not self._settings['only_instrumental'])
            if option == 'q':
                self.quit()
                continue
            if self.is_busy():
                if option == 'f':
                    self.favourite()
                if option == 'h':
                    self.hate()
                if option == 'n':
                    self.next()
                if option == 'p':
                    self.pause()

    def play_from_parent_genre(self):
        genres = self.get_parent_genres()
        self.choose_genre_from_list(genres)

    def play_genre_from_search(self):
        term = input("I'm feeling lucky: ")
        genres = self.search_genres(term)
        if not genres:
            print('no genres found')
            return
        self.choose_genre_from_list(genres)

    def status(self):
        print('status')
        print('is playing', self.pr.is_playing)
        print('is busy', self.pr.m.get_busy())
        print(self._settings)
        try:
            print(' genre', self.tb.genre.genre_title, self.tb.genre.genre_id)
            print(' track', self.track.track_title, self.track.track_id, self.track.track_duration)
        except:
            pass


if __name__ == '__main__':
    cli = CLI()
    cli.menu()
