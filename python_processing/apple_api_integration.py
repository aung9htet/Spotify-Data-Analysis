import os
import json
import time
import requests
from apple_music_auth import AppleMusicAuth

class AppleAPI():

    def __init__(self, end_point="", url=None, **params):
        """
            The following object is supposed to create a class for integration of spotify API
            into python. These includes web api, ad api and usage of playcount.
        """
        # general
        self.auth = AppleMusicAuth()
        self.dev_token = self.auth.createAuthToken()
        self.base_url = "https://api.music.apple.com/v1"
        self.session = requests.Session()

        # url to process
        self.end_point = end_point
        self.url = url if not url is None else os.path.join(self.base_url, self.end_point)
        self.params = params

    def update_url(self, end_point="", url=None):
        """
            The following method updates the url based on whether an endpoint is given or
            a url is given.
        """
        self.end_point = end_point
        self.url = url if not url is None else os.path.join(self.base_url, self.end_point)    

    def get_data(self):
        """
            The following method gets json data from spotify for specific url
        """
        self.session.headers.update({'Authorization': f'Bearer {self.dev_token}'})
        try:
            response = self.session.get(self.url, params=self.params, timeout=5)
            data = response.json()
            return data
        except Exception as e:
            print(e)
        # return data
    
    def get_storefronts(self):
        self.update_url(end_point="storefronts")
        self.url = "https://api.music.apple.com/v1/catalog/us/songs/1648562803"
        print(self.get_data())

apple = AppleAPI()
apple.get_storefronts()
    # def get_artist_data(self, artist_id):
    #     """
    #         The following method uses the artist id to get data of the artist.
    #     """
    #     end_point= f"artists/{artist_id}"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_artist_album(self, artist_id):
    #     """
    #         The following method uses the artist id to get data of the artist.
    #     """
    #     end_point= f"artists/{artist_id}/albums"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_playlist_data(self, playlist_id):
    #     """
    #         The following method uses the playlist id to get data of the playlist.
    #     """
    #     end_point= f"playlists/{playlist_id}"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_track_data(self, track_id):
    #     """
    #         The following method uses the track id to get data of the playlist.
    #     """
    #     end_point= f"tracks/{track_id}"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_track_audio_feature(self, track_id):
    #     """
    #         The following method uses the track id to get spotify's analysis of audio features.
    #     """
    #     end_point = f"audio-features/{track_id}"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_track_audio_analysis(self, track_id):
    #     """
    #         The following method uses the track id to get spotify's analysis audio.
    #     """
    #     end_point = f"audio-analysis/{track_id}"
    #     self.update_url(end_point=end_point)
    #     data = self.get_data()
    #     return data
    
    # def get_playcount(self, album_id):
    #     """
    #         The following method returns the total playcount for the album and for all the tracks
    #         in the album.
    #     """
    #     self.url = "https://api-partner.spotify.com/pathfinder/v1/query"
    #     self.params = {
    #         'operationName': 'queryAlbumTracks',
    #         'variables': json.dumps({
    #             'uri': f'spotify:album:{album_id}',
    #             'offset': 0,
    #             'limit': 999
    #         }),
    #         'extensions': json.dumps({
    #             'persistedQuery': {
    #                 'version': 1,
    #                 'sha256Hash': '3ea563e1d68f486d8df30f69de9dcedae74c77e684b889ba7408c589d30f7f2e'
    #             }
    #         })
    #     }
    #     data = self.get_data()
    #     print(self.get_data())

    #     album_playcount = {}

    #     for item in data['data']['album']['tracks']['items']:
    #         track = item['track']

    #         track_uri, playcount = track['uri'], track['playcount']
    #         album_playcount[track_uri] = int(playcount)

    #     total_playcount = sum(album_playcount.values())

    #     return album_playcount, total_playcount