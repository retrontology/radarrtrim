from radarr_client import radarr_client
from plexapi.myplex import PlexServer, NotFound
import ssl
from reyaml import yamlConf

CONFIG_FILE = 'config.yaml'

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
    # Load config
    config = yamlConf(CONFIG_FILE)
    config.save()
    
    # Patch SSL
    patch_ssl()

    # Clients
    radarr = radarr_client(config.radarr.ip,
                           config.radarr.port,
                           config.radarr.api_path, 
                           config.radarr.api_key)
    plex = PlexServer(config.plex.base_url, config.plex.token)

    # Trim
    remove_watched_movies(plex, radarr)
    radarr.remove_deleted_movies_from_queue()
    radarr.search_for_missing_movies()
    

if __name__ == '__main__':
    main()