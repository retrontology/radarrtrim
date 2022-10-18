from radarr_client import radarr_client
from plexapi.myplex import PlexServer, NotFound
import ssl
from retroyaml import yamlConf

CONFIG_FILE = 'config.yaml'

def patch_ssl():
    ssl.match_hostname = lambda cert, hostname: True

def remove_watched_movies_from_radarr_by_tmdb_id(plex:PlexServer, radarr:radarr_client):
    radarr_movies = radarr.get_movies()
    plex_movies = plex.library.section('Movies').search()
    watched_movies = list(filter(lambda x: x.isWatched, plex_movies))
    for watched_movie in watched_movies:
        watched_tmdb_id = None
        for guid in watched_movie.guids:
            if guid.id[:4] == 'tmdb':
                watched_tmdb_id = int(guid.id[7:])
        watched_movie.delete()
        print(f'removed {watched_movie.title} from plex')
        if watched_tmdb_id != None:
            for radarr_movie in radarr_movies:
                if radarr_movie['tmdbId'] == watched_tmdb_id:
                    radarr.delete_movie(radarr_movie['id'], addImportExclusion=True, deleteFiles=True)
                    print(f'removed {radarr_movie["title"]} from radarr')
                    break


def remove_watched_movies_from_radarr_by_title(plex:PlexServer, radarr:radarr_client):
    movies = radarr.get_movies()
    history = plex.library.section('Movies').history()
    for movie in movies:
        movie_titles = [movie['title'], movie['originalTitle']]
        if movie['originalTitle']:
            movie_titles.append(movie['originalTitle'])
        if movie['alternateTitles']:
            alt_titles = list(map(lambda x: x['title'], movie['alternateTitles']))
            movie_titles.extend(alt_titles)
        for watched in history:
            watched_titles = [watched.title]
            if watched.originalTitle:
                watched_titles.append(watched.originalTitle)
            for movie_title in movie_titles:
                for watched_title in watched_titles:
                    if movie_title == watched_title:
                        radarr.delete_movie(movie['id'], addImportExclusion=True, deleteFiles=True)
                        print(f'removed {movie["title"]} from radarr')
                        try:
                            plex.library.section('Movies').get(movie["title"]).delete()
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
    remove_watched_movies_from_radarr_by_tmdb_id(plex, radarr)

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