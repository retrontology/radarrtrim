from os import remove
from radarr_client import radarr_client
from plexapi.myplex import PlexServer, NotFound
import datetime
import ssl

RADARR_API_KEY = 'your radarr api key'
RADARR_IP = '192.168.1.1'
RADARR_PORT = 7878
RADARR_API_PATH = '/api/v3'

PLEX_TOKEN = 'your plex auth token'
PLEX_BASE_URL = 'your plex.direct url'

def patch_ssl():
    
    ssl.match_hostname = lambda cert, hostname: True

def remove_watched_movies(plex:PlexServer, radarr:radarr_client):
    movies = radarr.get_movies()
    for movie in movies:
        title = movie['title']
        isWatched = None
        try:
            isWatched = plex.library.section('Movies').get(title).isWatched
        except NotFound:
            for alt_title in movie['alternateTitles']:
                alt_title = alt_title['title']
                try:
                    isWatched = plex.library.section('Movies').get(alt_title).isWatched
                    title = alt_title
                    break
                except NotFound:
                    pass
        if isWatched == True:
            radarr.delete_movie(movie['id'], deleteFiles=True)

def main():
    patch_ssl()

    # Clients
    radarr = radarr_client(RADARR_IP, RADARR_PORT, RADARR_API_PATH, RADARR_API_KEY)
    plex = PlexServer(PLEX_BASE_URL, PLEX_TOKEN)

    # Get Movies
    #movies = radarr.get_movies_added_before(datetime.datetime.now() - datetime.timedelta(weeks=24))
    movies = radarr.get_movies()

    # Trim
    remove_watched_movies(plex, radarr)
    

if __name__ == '__main__':
    main()