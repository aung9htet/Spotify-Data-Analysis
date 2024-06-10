from spotify_api_intergration import SpotifyAPI

class ViewAnalysis(object):
    def __init__(self):
        self.api_integration = SpotifyAPI()
    
    def get_playcount_artist_by_id(self, artist_id):
        data = self.api_integration.get_artist_album(artist_id)['items']
        for album in data:
            album_id = album['id']
            album_playcount, track_playcount = self.api_integration.get_playcount(album_id)
            # print(album_playcount, track_playcount)

    def get_playcount_artist_by_uri(self, artist_uri):
        artist_id = artist_uri[15:]
        self.get_playcount_artist_by_id(artist_id)
    
    def get_account_id(self, account_id):
        self.api_integration.get_ad_account_data(account_id)

view = ViewAnalysis()
view.get_playcount_artist_by_uri("spotify:artist:1m7V9rstnZ264nGJe9MDUq")
# view.get_account_id("ce4ff15e-f04d-48b9-9ddf-fb3c85fbd57a")