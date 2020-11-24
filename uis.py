import browsers


import fmap


class CUISearch:
    def __init__(self, fmapy):
        self.download_count = 0
        self.fmapy = fmapy
        self.main()

    def main(self):
        searching = True
        while searching:
            search_term = input("What are you looking for: ")
            print(self.fmapy.browser.search(search_term))
            answer = input("Do you want to download them [Y/n]")
            if answer.lower() in ["y", ""]:
                searching = False

        for song in self.fmapy.browser:
            print("Downloading: ", song)
            try:
                filename = self.fmapy.download_song(song)
            except fmap.FmapyError:
                print("Failed to download:", song)
            else:
                if filename:
                    print("Ready at:", filename)
                    self.download_count += 1
                else:
                    print("Song in cache:", song)
        print("Downloaded: ", self.download_count, " songs")
