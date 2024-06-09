from old.spotify_api_buffer import SpotifyBuffer

class UserFlow(object):

    def __init__(self, uri):
        self.spotify_data = SpotifyBuffer()
        self.albums = self.spotify_data.get_artist_albums(uri)
        
    def get_stream_count(self):
        track_list = []
        for album in self.albums:
            album_uri = album['uri']
            album_data = self.spotify_data.get_album_tracks(album_uri)
            album_id = album['id']
            album_playcount = self.spotify_data.get_album_playcount(album_id)
            for track in album_data:
                track_list.append(track)
        for track in track_list[:1]:
            # print(track.keys())
            track_id = track['id']
            # print(track_id)
            url = "https://api.spotify.com/v1/tracks"
            params = {
                    'ids': track_id,
                    'market': 'SG'
                }
        print(self.spotify_data.get_data_json(url, **params))


if __name__ == '__main__':
    user_flow = UserFlow("spotify:artist:1m7V9rstnZ264nGJe9MDUq")
    user_flow.get_stream_count()