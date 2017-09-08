import os

import fmap


class BaseUI:

    def __init__(self):
        self._quit = False

        self.player = fmap.Player(self.song_ended, self.play_failed, self.check_if_playable_callback)

        self._items_by_category = {}

    def append_item_by_category(self, item, category, repeat=False):
        items = self.get_items_by_category(category)
        items.append(item.track_id)
        if not repeat:
            items = set(items)
        self.store_items_by_category(items, category)

    def favourite(self):
        self.append_item_by_category(self.player.track, 'favourites')

    def get_category_file_path(self, category):
        category_file_path = os.path.join(
            fmap.get_project_dir(category), category + '.txt'
        )
        return category_file_path

    def get_items_by_category(self, category):
        if category in self._items_by_category:
            return self._items_by_category[category]

        items_file_path = self.get_category_file_path(category)
        items = []
        try:
            items_file = open(items_file_path, 'r')
            items = [i.strip() for i in items_file.readlines()]
            items_file.close()
        except FileNotFoundError:
            pass

        self._items_by_category[category] = items
        return items

    def hate(self):
        self.append_item_by_category(self.player.track, 'hates')

    def is_busy(self):
        return self.player.is_busy()

    def is_favourite(self, track):
        return self.is_item_in_category(track, 'favourites')

    def is_hated(self, track):
        return self.is_item_in_category(track, 'hates')

    def is_item_in_category(self, item, category):
        items = self.get_items_by_category(category)
        return item.track_id in items

    def song_ended(self):
        self.append_item_by_category(self.player.track, 'endeds', repeat=True)

    def pause(self):
        self.player.pause()

    def check_if_playable_callback(self, track):
        if self.is_hated(track):
            print('haters gonna hate')
            return False
        if self.player.get_settings()['only_new'] and not self.track_is_new(track):
            print('skipping not new')
            return False
        if self.player.get_settings()['only_instrumental'] and not int(track.track_instrumental):
            print('skipping not instrumental')
            return False
        return True

    def play(self):
        self.player.play()

    def play_failed(self):
        self.append_item_by_category(self.player.track, 'failed', repeat=True)

    def next(self):
        self.append_item_by_category(self.player.track, 'skipped', repeat=True)
        self.player.next()

    def stop(self):
        self.player.stop()

    def store_items_by_category(self, items, category):
        del(self._items_by_category[category])
        items_file_path = self.get_category_file_path(category)
        items = '\n'.join(items)
        with open(items_file_path, 'w') as items_file:
            items_file.write(items)

    def track_is_new(self, track):
        return not self.is_item_in_category(track, 'endeds')

    def quit(self):
        self.stop()
        self._quit = True
