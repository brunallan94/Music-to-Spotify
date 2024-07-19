import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tkinter import Tk, filedialog
import re
import logging
from check_internet import check_internet_connection

logging.basicConfig(filename='app.log', level=logging.DEBUG, filemode='w', format="%(asctime)s -> %(levelname)s -> %(message)s")


class Music:
    def __init__(self, directory: str, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.directory = directory
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = 'playlist-modify-public'
        self.sp = None
        self.user_id = None

    def files(self) -> list[str]:
        try:
            files = [f for f in os.listdir(self.directory) if f.endswith(('.mp3', '.m4a'))]
            logging.debug(f'Found {len(files)} music files.')
            return files
        except Exception as e:
            logging.error(f'Error accessing directory {self.directory}: {e}')
            raise

    def extract_metadata(self) -> list[dict[str, Any]]:
        metadata_list: list = []
        for file in self.files():
            file_path: str = os.path.join(self.directory, file)
            try:
                audio = EasyID3(file_path)
                metadata_list.append({
                    'title': audio.get('title', [os.path.splitext(file)[0]])[0],
                    'artist': audio.get('artist', ['Unknown Artist'])[0]
                })
            except ID3NoHeaderError:
                title, artist = self.parse_filename(file)
                metadata_list.append({'title': title, 'artist': artist})
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                title, artist = self.parse_filename(file)
                metadata_list.append({'title': title, 'artist': artist})
        logging.info(metadata_list)
        return metadata_list

    def parse_filename(self, filename: str) -> tuple[str | Any, str | Any] | tuple[Any, str]:
        # Attempt to extract metadata from filename using regex pattern
        pattern = re.compile(r'(?P<artist>.+?) - (?P<title>.+)')
        match = pattern.match(os.path.splitext(filename)[0])
        logging.info(match)
        if match:
            return match.group('title'), match.group('artist')
        return os.path.splitext(filename)[0], 'Unknown Artist'

    def integrate_with_spotify(self) -> None:
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope
            ))
            self.user_id = self.sp.me()['id']
            logging.info(f'Successfully authenticated with Spotify as user {self.user_id}.')
        except Exception as e:
            logging.error(f'Error integrating with spotify: {e}')
            raise

    def create_playlist(self, playlist_name: str ='Local Tracks') -> str:
        self.integrate_with_spotify()

        try:
            # Check if the playlist already exists
            playlists = self.sp.user_playlists(self.user_id)
            for playlist in playlists['items']:
                if playlist['name'] == playlist_name:
                    logging.info(f"Playlist '{playlist_name}' already exists.")
                    return playlist['id']

            # If playlist does not exist, create it
            playlist = self.sp.user_playlist_create(user=self.user_id, name=playlist_name, public=True)
            logging.info(f'Created new playlist "{playlist_name}".')
            return playlist['id']
        except Exception as e:
            logging.error(f'Error creating playlist "{playlist_name}": {e}')
            raise

    def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        tracks: list = []
        try:
            results = self.sp.playlist_tracks(playlist_id)
            tracks.extend(results['items'])
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])
            return [track['track']['id'] for track in tracks]
        except Exception as e:
            logging.error(f'Error retrieving tracks from playlist {playlist_id}: {e}')
            raise

    def search_and_add_tracks(self, playlist_id: str) -> None:
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
    if not check_internet_connection():
        logging.error('No internet connection. Please check your connection and try again.')
        return

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
