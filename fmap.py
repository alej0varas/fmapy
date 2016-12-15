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
            i = get_dataset_item_class(self.dataset_name)()
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

    t = None
    is_playing = True
    tracks = None
    current_track_index = -1

    def __init__(self):
        self.q = False
        self.gb = GenresBrowser()
        self.tb = TrackBrowser()

        pygame.init()
        self.m = pygame.mixer.music
        self.t_stop = threading.Event()

        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        self._play_thread()

    def append_item_by_category(self, item, category):
        items = self.get_items_by_category(category)
        items.append(item.track_id)
        items = set(items)
        self.store_items_by_category(items, category)

    def choose_genre(self, genres):
        enumerated = self.enumerate_genres(genres)
        for index, genre in enumerated:
            print(index, genre.genre_title)
        option = int(input('Choose a genre: '))
        self.set_genre(enumerated[option][1])
        self.play()

    def choose_from_parent_genre(self):
        genres = self.get_parent_genres()
        self.choose_genre(genres)

    def choose_genre_from_search(self):
        term = input("I'm feeling lucky: ")
        genres = self.load_term_genres(term)
        if not genres:
            print('no genres found')
            return
        self.choose_genre(genres)

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

    def get_next_track(self):
        self.current_track_index += 1
        try:
            track = self.tracks[self.current_track_index]
        except IndexError:
            self.current_track_index -= 1
            self.load_tracks()
            return self.get_next_track()
        return track

    def get_parent_genres(self):
        genres = [g for g in self.gb.items if not g.genre_parent_id]
        return genres

    def get_track_file_name(self, track):
        project_dir = get_project_dir('cache')
        tmp_track_file_name = os.path.join(
            project_dir, str(track.track_id)
        ) + '.mp3'
        in_cache = True
        if not os.path.exists(tmp_track_file_name):
            in_cache = False
            with open(tmp_track_file_name, 'wb') as tmp_track:
                track = track.get_content(track.get_url(), json=False)
                tmp_track.write(track)
        print(tmp_track_file_name, ['not', 'in'][in_cache], 'cache')
        return tmp_track_file_name

    def hate(self):
        self.append_item_by_category(self.track, 'hates')

    def info(self):
        print(
            self.track.track_title, '|',
            self.track.artist_name, '|',
            self.track.album_title, '(',
            self.track.track_duration, ')<',
            self.track.track_id, '>',
        )

    def is_favourite(self, track):
        return self.is_item_in_category(track, 'favourites')

    def is_hated(self, track):
        return self.is_item_in_category(track, 'hates')

    def is_item_in_category(self, item, category):
        items = self.get_items_by_category(category)
        return item.track_id in items

    def load_random_genre(self):
        self.set_genre(random.choice(self.gb.items))

    def load_term_genres(self, term):
        genres = []
        for g in self.gb.items:
            if term.lower() in g.genre_title.lower():
                genres.append(g)
        return genres

    def load_tracks(self):
        self.tb.load_next_page()
        self.tracks = self.tb.items

    def pause(self):
        if self.is_playing:
            self.is_playing = False
            self.m.pause()
        else:
            self.is_playing = True
            self.m.unpause()

    def play(self):
        if self.tracks is None:
            self.load_tracks()
        track = self.get_next_track()
        if self.is_hated(track):
            print('haters gonna hate')
            self.info()
            self.next()
            return
        if self.is_favourite(track):
            print('lovers gonna love')
            self.info()

        track_file_name = self.get_track_file_name(track)
        try:
            self.m.load(track_file_name)
            self.m.play()
        except pygame.error as e:
            print(e)
            self.play()

    def play_random_genre(self):
        self.load_random_genre()
        self.play()

    def menu(self):
        while not self.q:
            option = input('>> ')
            if option == 'g':
                self.choose_from_parent_genre()
            if option == 'r':
                self.play_random_genre()
            if option == 's':
                self.choose_genre_from_search()
            if option == 'q':
                self.stop()
                continue
            if self.current_track_index > -1:
                if option == 'f':
                    self.favourite()
                if option == 'h':
                    self.hate()
                if option == 'i':
                    self.info()
                if option == 'n':
                    self.next()
                if option == 'p':
                    self.pause()

    def next(self):
        self.m.stop()
        self.play()

    def set_genre(self, genre):
        self.tracks = None
        self.tb.set_genre(genre)

    def stop(self):
        self.m.stop()
        self.t_stop.set()
        self.q = True

    def store_items_by_category(self, items, category):
        items_file_path = self.get_category_file_path(category)
        items = '\n'.join(items)
        with open(items_file_path, 'w') as items_file:
            items_file.write(items)

    @property
    def track(self):
        return self.tracks[self.current_track_index]

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
    p.menu()
