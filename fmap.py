import os
import requests


FMA_API_URL = 'https://freemusicarchive.org/api/get/{0}.{1}?api_key={2}'
FMA_API_KEY = os.environ.get('FMA_API_KEY')
FMA_API_FORMAT = os.environ.get('FMA_API_FORMAT', 'json')
FMA_API_DATASETS = ['artists', 'albums', 'tracks', 'genres', 'curators']
FMA_TRACK_SINGLE_URL = 'http://freemusicarchive.org/services/track/single/{0}.' + FMA_API_FORMAT


def get_dataset(option):
    return globals()['get_' + option]()


def get_content(url):
    response = requests.get(url)
    if response.ok:
        return response.json()  # will fail for other formats


def build_url(dataset):
    url = FMA_API_URL.format(dataset, FMA_API_FORMAT, FMA_API_KEY)
    return url


def get_tracks():
    url = build_url('tracks')
    data = get_content(url)
    return data['dataset']


def get_track_url(id):
    content = get_content(FMA_TRACK_SINGLE_URL.format(id))
    return content['track_listen_url']
    import pdb; pdb.set_trace()


def get_genres():
    url = build_url('genres')
    dataset = get_dataset(url)
    

def play(url):
    import subprocess
    subprocess.Popen(['mpv', '--no-video', '--no-terminal', url]).wait()

    
if __name__ == '__main__':
    print(list(enumerate(FMA_API_DATASETS)))
    option = int(input('Choose a datasat'))
    dataset = get_dataset(FMA_API_DATASETS[option])
    for item in dataset:
        track_url = get_track_url(item['track_id'])
        play(track_url)
