import requests
import logging
import re
import datetime

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATE_REGEX = '[0-9]{4}(-[0-9]{2}){2}T([0-9]{2}:){2}[0-9]{2}Z'
DEFAULT_PAGE_SIZE = 20
DEFAULT_SORT_DIRECTION = 'ascending'
DEFAULT_QUEUE_SORT_KEY = 'timeLeft'
DEFAULT_INCLUDE_UNKNOWN_MOVIE_ITEMS = True

class radarr_client():

    logger = logging.getLogger('radarr_client')
    date_expression = re.compile(DATE_REGEX)

    def __init__(self, ip, port, path, key):
        self.ip = ip
        self.port = port
        self.path = path
        self.key = key
        self.session = requests.Session()
        self.session.params = {'apikey': self.key}

    def get_url(self, operation=None):
        return f'http://{self.ip}:{self.port}{self.path}{operation}'

    def delete_movie(self, id, addImportExclusion=False, deleteFiles=False):
        self.delete(f'/movie/{id}', addImportExclusion=addImportExclusion, deleteFiles=deleteFiles)

    def get_movies(self, tmdbId = None):
        return self.get('/movie', tmdbId = tmdbId)
    
    def get_movies_added_before(self, cutoff):
        movies = sorted(self.get_movies(), key = lambda x: x['added'], reverse=True)
        for i in range(len(movies)):
            if movies[i]['added'] < cutoff:
                movies = movies[:i]
                break
        return movies
    
    def get_queue(self, pageSize = DEFAULT_PAGE_SIZE, sortDirection = DEFAULT_QUEUE_SORT_KEY, sortKey = DEFAULT_QUEUE_SORT_KEY, includeUnknownMovieItems = DEFAULT_INCLUDE_UNKNOWN_MOVIE_ITEMS):
        return self.get_paginated_results('/queue', pageSize = pageSize, sortDirection = sortDirection, sortKey = sortKey, includeUnknownMovieItems = includeUnknownMovieItems)
    
    def get_queue_details(self, includeMovie=True):
        return self.get('/queue/details', includeMovie=includeMovie)

    def get_queue_status(self):
        return self.get('/queue/status')

    def search_for_missing_movies(self):
        #self.post('/command', {'name': 'MissingMoviesSearch'})
        movies = self.get_movies()
        queue = list(map(lambda x: x['movieId'], self.get_queue(includeUnknownMovieItems = False)))
        missing = []
        for movie in movies:
            if movie['monitored'] and movie['status'] == 'released' and not movie['hasFile'] and movie['id'] not in queue:
                missing.append(movie)
        if len(missing) > 0:
            missing_ids = list(map(lambda x: x['id'], missing))
            missing_names = list(map(lambda x: x['title'], missing))
            self.post('/command', {'name': 'MoviesSearch', 'movieIds': missing_ids})
            print(f'Searching for: {", ".join(missing_names)}')
    
    def get_paginated_results(self, operation, **kwargs):
        page_number = 1
        page_end = False
        records = []
        while not page_end:
            kwargs['page'] = page_number
            results = self.get(operation, **kwargs)
            records.extend(results['records'])
            if results['page'] * results['pageSize'] >= results['totalRecords']:
                page_end = True
            else:
                page_number += 1
        return records

    def remove_deleted_movies_from_queue(self):
        queue = self.get_queue(includeUnknownMovieItems=True)
        queue = list(filter(lambda x: 'movieId' not in x, queue))
        queue = list(map(lambda x: x['id'], queue))
        if len(queue) == 1:
            self.remove_from_queue(queue[0])
        elif len(queue) > 1:
            self.remove_from_queue_bulk(queue)

    def remove_from_queue(self, id, removeFromClient=True, blocklist=False):
        return self.delete(f'/queue/{id}',
                            removeFromClient=removeFromClient,
                            blocklist=removeFromClient)

    def remove_from_queue_bulk(self, ids, removeFromClient=True, blocklist=False):
        return self.delete(f'/queue/bulk',
                            json={'ids': ids},
                            removeFromClient=removeFromClient,
                            blocklist=blocklist)
    
    def get(self, operation, **kwargs):
        response = self.session.get(
            url = self.get_url(operation),
            params = kwargs
        )
        match response.status_code:
            case 200:
                return self.parse_json(response.json())
            case _:
                return response
    
    def delete(self, operation, json=None, **kwargs):
        response = self.session.delete(
            url = self.get_url(operation),
            json=json,
            params = kwargs
        )
        match response.status_code:
            case 200:
                return True
            case _:
                return False
    
    def post(self, operation, json, **kwargs):
        response = self.session.post(
            url = self.get_url(operation),
            json=json,
            params = kwargs
        )
        match response.status_code:
            case 200 | 201:
                return self.parse_json(response.json())
            case _:
                return response
    
    
    @classmethod
    def parse_json(cls, obj):
        if issubclass(type(obj), dict):
            iter_obj = obj.keys()
        elif issubclass(type(obj), list):
            iter_obj = range(len(obj))
        else:
            return obj
        for key in iter_obj:
            obj[key] = cls.parse_json(obj[key])
            if issubclass(type(obj[key]), str):
                if cls.date_expression.fullmatch(obj[key]):
                    obj[key] = datetime.datetime.strptime(obj[key], DATE_FORMAT)
        return obj
