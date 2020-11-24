class Cache:
    def __init__(self, path, items):
        self._path = path
        self._items = items

    def __contains__(self, item):
        return item in self._items

    def write(self, item):
        with open(self._path, "a") as cache_file:
            cache_file.write(item + "\n")
