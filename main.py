import os
from dotenv import load_dotenv
from mutagen.easyid3 import EasyID3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tkinter import Tk, filedialog


class Music:
    def __init__(self, directory, client_id, client_secret, redirect_uri) -> None:
        self.directory = directory
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = 'playlist-modify-public'
        self.sp = None
        self.user_id = None

    def files(self):
        return [f for f in os.listdir(self.directory) if f.endswith('.mp3')]

    def extract_metadata(self):
        metadata_list = []
        for file in self.files():
            file_path = os.path.join(self.directory, file)
            try:
                audio = EasyID3(file_path)
                metadata_list.append({
                    'title': audio.get('title', [os.path.splitext(file)[0]])[0],
                    'artist': audio.get('artist', ['Unknown Artist'])[0]
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return metadata_list

    def integrate_with_spotify(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        ))
        self.user_id = self.sp.me()['id']

    def create_playlist(self, playlist_name='Local Tracks'):
        self.integrate_with_spotify()

        # Check if the playlist already exists
        playlists = self.sp.user_playlists(self.user_id)
        for playlist in playlists['items']:
            if playlist['name'] == playlist_name:
                print(f"Playlist '{playlist_name}' already exists.")
                return playlist['id']

        # If playlist does not exist, create it
        playlist = self.sp.user_playlist_create(user=self.user_id, name=playlist_name, public=True)
        print(f'Created new playlist "{playlist_name}".')
        return playlist['id']

    def get_playlist_tracks(self, playlist_id):
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        tracks.extend(results['items'])
        while results['next']:
            results = self.sp.next(results)
            tracks.extend(results['items'])
        return [track['track']['id'] for track in tracks]

    def search_and_add_tracks(self, playlist_id):
        existing_track_ids = self.get_playlist_tracks(playlist_id)
        metadata_list = self.extract_metadata()
        for metadata in metadata_list:
            query = f"{metadata['title']} {metadata['artist']}"
            results = self.sp.search(q=query, type='track', limit=1)
            tracks = results['tracks']['items']
            if tracks:
                track = tracks[0]
                track_name = track['name']
                track_artist = track['artists'][0]['name']
                track_id = track['id']
                if track_id not in existing_track_ids:
                    print(f'Adding track: {track_name} by {track_artist}')
                    self.sp.playlist_add_items(playlist_id, [track_id])
                else:
                    print(f'Track already exists: {track_name} by {track_artist}')


def configure() -> None:
    load_dotenv()


def main() -> None:
    configure()

    root = Tk()
    root.withdraw()  # Hide the root window

    directory = filedialog.askdirectory(title="Select Directory with Music Files")
    if not directory:
        raise ValueError("No directory selected.")

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError('Please set the SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI environment variables.')

    music = Music(directory, client_id, client_secret, redirect_uri)
    playlist_id = music.create_playlist()
    music.search_and_add_tracks(playlist_id)


if __name__ == "__main__":
    main()
