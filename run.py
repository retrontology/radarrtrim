from os import remove
from radarr_client import radarr_client
from plexapi.myplex import PlexServer, NotFound
import ssl

RADARR_API_KEY = 'your radarr api key'
RADARR_IP = '192.168.1.1'
RADARR_PORT = 7878
RADARR_API_PATH = '/api/v3'

PLEX_TOKEN = 'your plex auth token'
PLEX_BASE_URL = 'your plex.direct url'

def patch_ssl():
    ssl.match_hostname = lambda cert, hostname: True

def remove_watched_movies_from_radarr(plex:PlexServer, radarr:radarr_client):
    movies = radarr.get_movies()
    history = plex.library.section('Movies').history()
    for movie in movies:
        titles = [movie['title']]
        alt_titles = list(map(lambda x: x['title'], movie['alternateTitles']))
        titles.extend(alt_titles)
        for watched in history:
            for title in titles:
                if title == watched.title:
                    radarr.delete_movie(movie['id'], deleteFiles=True)
                    print(f'removed {movie["title"]} from radarr')
                    try:
                        plex.library.section('Movies').get(title).delete()
                        print(f'removed {movie["title"]} from plex')
                    except NotFound:
                        pass

def remove_watched_movies_from_plex(plex:PlexServer):
    movies = plex.library.section('Movies').all()
    for movie in movies:
        if movie.isWatched:
            deleted = False
            while not deleted:
                try:
                    movie.delete()
                    print(f'removed {movie.title} from plex')
                    deleted = True
                except Exception as e:
                    print(e)

def remove_watched_movies(plex:PlexServer, radarr:radarr_client):
    remove_watched_movies_from_radarr(plex, radarr)
    remove_watched_movies_from_plex(plex)

def main():
    patch_ssl()

    # Clients
    radarr = radarr_client(RADARR_IP, RADARR_PORT, RADARR_API_PATH, RADARR_API_KEY)
    plex = PlexServer(PLEX_BASE_URL, PLEX_TOKEN)

    # Trim
    remove_watched_movies(plex, radarr)
    radarr.search_for_missing_movies()
    

if __name__ == '__main__':
    main()