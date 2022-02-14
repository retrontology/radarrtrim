from collections.abc import Sequence
import requests
import logging
import re
import datetime

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATE_REGEX = '[0-9]{4}(-[0-9]{2}){2}T([0-9]{2}:){2}[0-9]{2}Z'

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
    
    def delete(self, operation, **kwargs):
        response = self.session.delete(
            url = self.get_url(operation),
            params = kwargs
        )
        match response.status_code:
            case 200:
                return True
            case _:
                return False
    
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
