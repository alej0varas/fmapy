import logging

import baseui


class CLI(baseui.BaseUI):

    def choose_genre_from_list(self, genres):
        logging.debug('CLI.choose_genre_from_list')
        enumerated = self.player.enumerate_genres(genres)
        for index, genre in enumerated:
            print(index, genre.genre_title)
        while True:
            option = input('Choose a genre: ')
            try:
                option = int(option)
                self.player.set_genre(enumerated[option][1])
                break
            except (ValueError, IndexError):
                print(':/')

    def menu(self):
        logging.debug('CLI.menu')
        while True:
            option = input('>> ')
            if option == 'g':
                self.play_genre_from_parents()
            if option == 'o':
                self.player.settings(only_new=not self.player.get_settings()['only_new'])
            if option == 'r':
                self.player.play_random_genre()
            if option == 's':
                self.play_genre_from_search()
            if option == 't':
                self.stop()
            if option == 'a':
                self.play()
            if option == 'i':
                self.player.settings(only_instrumental=not self.player.get_settings()['only_instrumental'])
            if option == '?':
                self.print_help()
            if option == 'q':
                self.quit()
                break
            if self.player.is_busy():
                if option == 'f':
                    self.favourite()
                if option == 'h':
                    self.hate()
                if option == 'n':
                    self.next()
                if option == 'p':
                    self.pause()
            if option == '':
                self.status()

    def play_genre_from_parents(self):
        logging.debug('CLI.play_genre_from_parents')
        genres = self.player.get_parent_genres()
        self.choose_genre_from_list(genres)
        self.play()

    def play_genre_from_search(self):
        logging.debug('CLI.play_genre_from_search')
        term = input("I'm feeling lucky: ")
        genres = self.player.search_genres(term)
        if not genres:
            print('no genres found')
            return
        self.choose_genre_from_list(genres)
        self.play()

    def status(self):
        logging.debug('CLI.status')
        logging.debug('is playing ' + str(self.player.is_playing))
        logging.debug('is busy ' + str(self.player.mixer.get_busy()))
        logging.debug(str(self.player.get_settings()))
        print('Settings', self.player.get_settings())
        try:
            print(' Playing:', self.player.track.track_title, self.player.track.track_id, self.player.get_pos(), self.player.track.track_duration)
            print(' Genre:', self.player.track_browser.genre.genre_title, self.player.track_browser.genre.genre_id)
        except:
            pass

    def print_help(self):
        logging.debug('CLI.print_help')
        print('g - play genre from parents')
        print('o - settings: play only new songs')
        print('r - play random genre')
        print('s - search genre')
        print('t - stop playing')
        print('a - play')
        print('i - settings: play only instrumental')
        print('? - show help')
        print('q - quit')
        print('f - mark song as favourite')
        print('h - mark song as hated')
        print('n - play next song')
        print('p - pause')


if __name__ == '__main__':
    cli = CLI()
    cli.menu()
