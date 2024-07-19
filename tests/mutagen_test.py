from typing import List, Dict, Any
import logging
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import os
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from pprint import pprint
import re

logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG, format='%(asctime)s -> %(levelname)s -> %(message)s')


def files(directory) -> list[str]:
    return [f for f in os.listdir(directory) if f.endswith(('.mp3', '.m4a'))]


def configure() -> str:
    load_dotenv()
    return os.getenv('DIRECTORY')


def main() -> list[dict[str, Any]]:
    directory = configure()
    if directory:
        metadata_list: list = []
        for file in files(directory):
            file_path: str = os.path.join(directory, file)
            try:
                audio = EasyID3(file_path)
                metadata_list.append({
                    'title': audio.get('title', [os.path.splitext(file)[0]])[0],
                    'artist': audio.get('artist', ['Unknown Artist'])[0]
                })
            except ID3NoHeaderError:
                title, artist = parse_filename(file)
                metadata_list.append({'title': title, 'artist': artist})
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                title, artist = parse_filename(file)
                metadata_list.append({'title': title, 'artist': artist})
            logging.info(metadata_list)
        return metadata_list

    else:
        print("No directory found in environment variables.")


def parse_filename(filename) -> tuple[str | Any, str | Any] | tuple[Any, str]:
    # Attempt to extract metadata from filename using regex pattern
    pattern = re.compile(r'(?P<artist>.+?) - (?P<title>.+)')
    match = pattern.match(os.path.splitext(filename)[0])
    logging.info(match)
    if match:
        return match.group('title'), match.group('artist')
    return os.path.splitext(filename)[0], 'Unknown Artist'


if __name__ == '__main__':
    pprint(main())
