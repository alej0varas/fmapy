class Cache:
    def __init__(self, path):
        self._path = path

    def __contains__(self, item):
        with open(self._path) as cache_file:
            return item in map(str.strip, cache_file.readlines())

    def write(self, item):
        with open(self._path, "a") as cache_file:
            cache_file.write(item + "\n")
