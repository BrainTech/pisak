"""
Movies library management.
"""
import os.path
import subprocess
import threading
import re

from pisak import logger, res, dirs, media_library, utils


_LOG = logger.get_logger(__name__)


ACCEPTED_TYPES = [
    ".mp4", ".avi", ".mkv", ".mpeg", ".ogg"
]


SUBTITLE_EXTENSIONS = [
    "txt", "srt"
]


LIBRARY_DIR = dirs.get_user_dir("videos")


FAVOURITE_MOVIES_STORE = os.path.join(dirs.HOME_PISAK_FAVOURITES, "favourite_movies.ini")


FAVOURITE_MOVIES_ALIAS = "ULUBIONE"


FAKE_COVER_NAME = "fake_cover.png"


COVER_EXTENSIONS = ["png", "jpg", "jpeg", "bmp"]


_LIBRARY_STORE = {}


class _Library(media_library.Library):

    def __init__(self, *args, **kwargs):
        self._worker = None
        self._lock = threading.RLock()
        self._to_be_framed = []
        super().__init__(exec_for_all=self.assign_cover, *args, **kwargs)

    def find_subtitles(self, movie_path):
        """
        Find subtitles for a movie.

        :param movie_path: path to a movie.

        :return: path to subtitles or None if nothing found.
        """
        base_path = os.path.splitext(movie_path)[0]
        for ext in SUBTITLE_EXTENSIONS:
            path = ".".join([base_path, ext])
            if os.path.isfile(path):
                return path

    def assign_cover(self, folder, movie, movie_path, folder_path, folder_name, dir_files):
        """
        Find and set a cover picture for a given movie.

        :param folder: folder instance.
        :param movie: movie instance as a library item.
        :param movie_path: path to the movie.
        :param folder_path: path to a folder that contains the movie.
        :param folder_name: name of the folder.
        :path dir_file: list of all the files in the directory.
        """
        naked_movie_path = os.path.splitext(movie_path)[0]
        cover_path = self._find_cover(naked_movie_path, COVER_EXTENSIONS)
        if not cover_path:
            cover_path = '.'.join([naked_movie_path, COVER_EXTENSIONS[0]])
            self._produce_cover(movie_path, cover_path)
        movie.extra['cover'] = cover_path

    def _find_cover(self, naked_movie_path, cover_extensions):
        for ext in cover_extensions:
            possible_covers = ['.'.join([naked_movie_path, ext.lower()]),
                               '.'.join([naked_movie_path, ext.upper()])]
            for cover in possible_covers:
                if os.path.isfile(cover):
                    return cover

    # - movie frames extraction or identicons generation in a separate thread - #

    def _produce_cover(self, movie_path, cover_path):
        def do_work():
            while True:
                with self._lock:
                    if self._to_be_framed:
                        movie_path, cover_path = self._to_be_framed.pop(0)
                    else:
                        self._worker = None
                        break
                if not self._extract_single_frame(movie_path, cover_path):
                    utils.produce_identicon(movie_path, save_path=cover_path)

        with self._lock:
            self._to_be_framed.append((movie_path, cover_path))

        if not self._worker:
            self._worker = threading.Thread(target=do_work, daemon=True)
            self._worker.start()

    def _extract_single_frame(self, movie_path, frame_path):
        conversing_engine = "avconv"
        # wait for generation of frame image for no
        # longer than this number of seconds:
        patience_level = 2
        # time from which the frame should be taken (in seconds):
        time = '180'
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

    # ------------------------------------------------------------------------- #


def get_library():
    """
    Get the movie library.

    :return: library instance.
    """
    try:
        library = _LIBRARY_STORE[LIBRARY_DIR]
    except KeyError:
        library = _Library(
            LIBRARY_DIR, ACCEPTED_TYPES, FAVOURITE_MOVIES_STORE, FAVOURITE_MOVIES_ALIAS)
        library.include_favs()
        _LIBRARY_STORE[LIBRARY_DIR] = library
    return library
