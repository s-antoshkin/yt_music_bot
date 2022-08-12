import re
from pathlib import Path

from pytube import YouTube, Playlist
from aiogram import types


DOWNLOAD_DIR = Path(__file__).resolve().parent / 'files'

YOUTUBE_STREAM_AUDIO = '140'


def set_type_link(link):
    match = re.search('/watch', link)
    return 'song' if match != None else 'playlist'


def set_dir(user_id):
    user_dir = DOWNLOAD_DIR / ('files_' + str(user_id))
    user_dir.parent.mkdir(parents=True, exist_ok=True)
    return user_dir
    
def songs_count(link):
    link_type = set_type_link(link)
    if link_type == 'song':
        return 1
    playlist = Playlist(link)
    return len(playlist.video_urls) if playlist else 0


def create_song_list(user_id, link, count=0):
    user_dir = set_dir(user_id)
    link_type = set_type_link(link)
    files = []
    if link_type != 'song':
        playlist = Playlist(link)
        if not playlist: return
        playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
        for i in range(count):
            try:
               download_song(user_dir, playlist.videos[i])
            except:
                continue 
    else:
        video = YouTube(link)
        download_song(user_dir, video)

    convert_to_mp3(user_dir)
    for file in user_dir.iterdir():
        files.append(file)
    
    files_list = chunks_generator(files, 10)
    song_list = [create_media_group(files_pack) for files_pack in files_list]
    return song_list


def chunks_generator(lst, count=10):
    for i in range(0, len(lst), count):
        yield lst[i : i + count]


def create_media_group(media_list):
    media = types.MediaGroup()
    for file in media_list:
        media.attach_audio(types.InputMediaAudio(file.open('rb')))
    return media


def download_song(user_dir, video):
    audioStream = video.streams.get_by_itag(YOUTUBE_STREAM_AUDIO)
    audioStream.download(output_path=user_dir)

def convert_to_mp3(user_dir):
    for file in user_dir.iterdir():
        if file.is_file():
            file.rename(file.with_suffix('.mp3'))


def delete_songs(user_id):
    user_dir = set_dir(user_id)
    if not user_dir.is_dir(): return
    for file in user_dir.iterdir():
        if file.is_file():
            file.unlink()
    user_dir.rmdir()
