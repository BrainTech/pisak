import os.path
import subprocess
import re

from pisak import logger, res, dirs, media_library, utils


_LOG = logger.get_logger(__name__)

ACCEPTED_TYPES = [
    "video/mp4", "video/x-msvideo", "video/mpeg",
    "video/x-matroska", "application/ogg"]


SUBTITLE_EXTENSIONS = [
    "txt", "srt"]


LIBRARY_DIR = dirs.get_user_dir("videos")


FAVOURITE_MOVIES_STORE = os.path.join(dirs.HOME_PISAK_FAVOURITES, "favourite_movies.ini")


FAVOURITE_MOVIES_ALIAS = "ULUBIONE"


FAKE_COVER_NAME = "fake_cover.png"


COVER_EXTENSIONS = ["png", "jpg", "jpeg", "bmp"]


_LIBRARY_STORE = {}


def get_library():
    try:
        library = _LIBRARY_STORE[LIBRARY_DIR]
    except KeyError:
        library = media_library.Library(LIBRARY_DIR, ACCEPTED_TYPES, FAVOURITE_MOVIES_STORE,
                          FAVOURITE_MOVIES_ALIAS, assign_cover)
        library.include_favs()
        _LIBRARY_STORE[LIBRARY_DIR] = library
    return library


def find_subtitles(movie_path):
    base_path = os.path.splitext(movie_path)[0]
    for ext in SUBTITLE_EXTENSIONS:
        path = ".".join([base_path, ext])
        if os.path.isfile(path):
            return path


def assign_cover(folder, movie, movie_path, folder_path, folder_name, dir_files):
    naked_movie_path = os.path.splitext(movie_path)[0]
    cover_path = _find_cover(naked_movie_path, COVER_EXTENSIONS)
    if not cover_path:
        cover_path = ".".join([naked_movie_path, COVER_EXTENSIONS[0]])
        if not _extract_single_frame(movie_path, cover_path):
            utils.produce_identicon(movie_path, save_path=cover_path)
    movie.extra["cover"] = cover_path


def _find_cover(naked_movie_path, cover_extensions):
    for ext in cover_extensions:
        possible_covers = [".".join([naked_movie_path, ext.lower()]), ".".join([naked_movie_path, ext.upper()])]
        for cover in possible_covers:
            if os.path.isfile(cover):
                return cover


def _extract_single_frame(movie_path, frame_path):
    probing_engine = "avprobe"
    conversing_engine = "avconv"
    # wait for generation of frame image for no
    # longer than this number of seconds:
    patience_level = 2
    cmd_length = [probing_engine,
                "-v", "quiet",
                "-show_format_entry", "duration",
                movie_path]
    probe = subprocess.Popen(cmd_length, stdout = subprocess.PIPE)
    out = probe.stdout.readline()
    if out:
        match = re.findall("\d+.\d+", str(out))
        if len(match) > 0:
            time = str(float(match[0]) / 2)
            cmd_frame = [conversing_engine,
                    "-v", "quiet",
                    "-ss", time,
                    "-i", movie_path,
                    "-t", "1",
                    "-r", "1",
                    frame_path]
            try:
                subprocess.call(cmd_frame, timeout=patience_level)
                if os.path.isfile(frame_path):
                    return True
            except subprocess.TimeoutExpired:
                pass  # assume the frame file was not created properly
    return False
