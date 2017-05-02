import baseui


class CLI(baseui.BaseUI):

    def choose_genre_from_list(self, genres):
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
        while True:
            self.status()
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

    def play_genre_from_parents(self):
        genres = self.get_parent_genres()
        self.choose_genre_from_list(genres)
        self.play()

    def play_genre_from_search(self):
        term = input("I'm feeling lucky: ")
        genres = self.player.search_genres(term)
        if not genres:
            print('no genres found')
            return
        self.choose_genre_from_list(genres)
        self.play()

    def status(self):
        print('status')
        print('is playing', self.player.is_playing)
        print('is busy', self.player.mixer.get_busy())
        print(self.player.get_settings())
        try:
            print(' genre', self.player.track_browser.genre.genre_title, self.player.track_browser.genre.genre_id)
            print(' track', self.player.track.track_title, self.player.track.track_id, self.player.track.track_duration)
        except:
            pass


if __name__ == '__main__':
    cli = CLI()
    cli.menu()
