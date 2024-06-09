import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import urllib
from urllib.request import urlopen
import json
import requests
import old.auth_spotify as auth_spotify

class SpotifyBuffer(object):

    def __init__(self):
        """
            The following class gets data from the spotify api to be used for the project. This part may be used
            as a backend and thus have Client Authorization Code Flow.
        """
        
        # use spotify api
        scope = "user-library-read"
        self.api_get = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=auth_spotify.CLIENT_ID,
                                                                 client_secret=auth_spotify.CLIENT_SECRET,
                                                                 redirect_uri=auth_spotify.REDIRECT_URI,
                                                                 scope=scope))
        
        # token path
        current_directory = os.getcwd()
        self.path_to_save = os.path.join(current_directory, ".cache")

    def get_access_token(self):
        """
            The following method uses the cached access token from spotipy
        """
        with open(self.path_to_save) as f:
            token = json.load(f)
        access_token = token['access_token']
        return access_token

    def get_playlist(self, uri):
        """
            The following method gets playlist data from the given uri
        """
        results = self.api_get.playlist_items(uri)
        tracks = results['items']
        return tracks
    
    def get_artist(self, uri):
        """
            The following method gets artist data from the given uri
        """
        results = self.api_get.artist(uri)
        return results
    
    def get_artist_albums(self, uri):
        """
            The following method gets the artist's list of albums from the given uri
        """
        results = self.api_get.artist_albums(uri)
        albums = results['items']
        return albums
    
    def get_album_tracks(self, uri):
        """
            The following method gets album data's track from the given uri
        """
        results = self.api_get.album_tracks(uri)
        tracks = results['items']
        return tracks
    
    def get_album(self, uri):
        """
            The following method gets album data from the given uri
        """
        results = self.api_get.album(uri)
        return results
    
    def post_data(self,url, data, headers={'Content-Type':'application/json'}):
        """
        POST data string to `url`, return page and headers
        """
        data = json.dumps(data)
        # if data is not in bytes, convert to it to utf-8 bytes
        bindata = data if type(data) == bytes else data.encode('utf-8')
        # need Request to pass headers
        req = urllib.request.Request(url, bindata, headers)
        resp = urllib.request.urlopen(req)
        return resp.read(), resp.getheaders()
    
    def get_data_json(self, url, **params):
        """
            The following method gets track data from given url. This uses spotify web
            json data sent from server to client
        """

        access_token = self.get_access_token()

        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {access_token}'})
        response = session.get(url, params=params, timeout=5)
        try:
            response = response.json()
        except:
            print(response)
        return response

    def get_album_playcount(self, album_id):
        url = "https://api-partner.spotify.com/pathfinder/v1/query"
        params = {
            'operationName': 'queryAlbumTracks',
            'variables': json.dumps({
                'uri': f'spotify:album:{album_id}',
                'offset': 0,
                'limit': 999
            }),
            'extensions': json.dumps({
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '3ea563e1d68f486d8df30f69de9dcedae74c77e684b889ba7408c589d30f7f2e'
                }
            })
        }
        data = self.get_data_json(url, **params)
