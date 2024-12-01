from radarr_client import radarr_client
from plexapi.myplex import PlexServer, NotFound
import ssl
from retroyaml.yamlConf import yamlConf

CONFIG_FILE = 'config.yaml'
RATING_CUTOFF = 7.0

def patch_ssl():
    ssl.match_hostname = lambda cert, hostname: True

def remove_watched_movies(plex:PlexServer, radarr:radarr_client):

    radarr_movies = radarr.get_movies()
    plex_movies = plex.library.section('Movies').search()

    watched_movies = list(
        filter(
            lambda x: x.isWatched and x.userRating < RATING_CUTOFF, plex_movies
        )
    )

    for watched_movie in watched_movies:

        watched_movie.tmdb_id = None
        for guid in watched_movie.guids:
            if guid.id[:4] == 'tmdb':
                watched_movie.tmdb_id = int(guid.id[7:])
                break
        
        if watched_movie.tmdb_id:
            if watched_movie.tmdb_id != None:
                for radarr_movie in radarr_movies:
                    if radarr_movie['tmdbId'] == watched_movie.tmdb_id:
                        radarr.delete_movie(radarr_movie['id'], addImportExclusion=True, deleteFiles=True)
                        print(f'removed {radarr_movie["title"]} from radarr')
                        break

        watched_movie.delete()
        print(f'removed {watched_movie.title} from plex')

        

def main():
    # Load config
    config = yamlConf(CONFIG_FILE)
    
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
