"""
Music loading.
"""
import os
import re
import time
import configobj

import taglib

from pisak import res, dirs, utils, logger
from pisak.audio import db_manager


_LOG = logger.get_logger(__name__)


_LIBRARY_DIR = dirs.get_user_dir("music")

_COVER_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".bmp"]

_LOAD_TRACKER = os.path.join(dirs.HOME_PISAK_DIR, "music_load_tracker.ini")

_FAKE_COVER_NAME = "fake_cover.png"

_UNKNOWN_LITERAL_TAG = "nieznane"

_UNKNOWN_NUMERICAL_TAG = 0


def load_all():
    """
    Load information about the music library in the filesystem and
    insert them to the database.
    """
    last_load_time = _get_last_load_time()
    tracks = list()
    db = db_manager.DBLoader()
    for current in [_LIBRARY_DIR] + os.listdir(_LIBRARY_DIR):
        if current is not _LIBRARY_DIR:
            current = os.path.join(_LIBRARY_DIR, current)
        if os.path.isdir(current) and os.path.getmtime(current) > last_load_time:
            # use os.walk here only to find all the files in
            # the current directory:
            for _, _, files in os.walk(current):
                if files:
                    folder_name = os.path.split(current)[-1]
                    cover_path = utils.find_folder_image(
                        files, folder_name.lower(), current, _COVER_EXTENSIONS)
                    if not cover_path:
                        cover_path = os.path.join(current, _FAKE_COVER_NAME)
                        utils.produce_identicon(current, save_path=cover_path)
                    folder_id = db.insert_folder(folder_name, cover_path)
                    for file_name in files:
                        path = os.path.join(current, file_name)
                        meta = _get_metadata(path, file_name)
                        if meta:
                            meta.update({'path': path,
                                         'cover_path': cover_path,
                                         'folder_id': folder_id})
                            tracks.append(meta)
                break
    # tracks = sorted(tracks, key=lambda k: k['path'].split("/")[-2]) #sortuje liste według indeksu w nazwie albumu
    db.insert_many_tracks(tracks)
    db.close()
    _update_last_load_time(time.time())


def _get_last_load_time():
    if not os.path.isfile(_LOAD_TRACKER):
        return 0
    else:
        return configobj.ConfigObj(
            _LOAD_TRACKER, encoding='UTF8').as_float("last_load_time")


def _update_last_load_time(time):
    conf = configobj.ConfigObj(_LOAD_TRACKER, encoding='UTF8')
    conf["last_load_time"] = time
    conf.write()


def _get_metadata(path, file_name):
    try:
        file_tags = taglib.File(path).tags
    except OSError:
        _LOG.warning("Taglib could not read file: {}.".format(path))
        return False
    metadata = dict()
    for tag, func in _TAG_EXTRACTORS.items():
        func(tag, metadata, file_tags, file_name)
    return metadata


def _extract_title(tag, metadata, file_tags, file_name):
    if _extract_literal_tag(tag, metadata, file_tags):
        return
    metadata["title"] = os.path.splitext(file_name)[0]


def _extract_tracknumber(tag, metadata, file_tags, file_name):
    if _extract_numerical_tag(tag, metadata, file_tags, 'no'):
        return
    no = _extract_number(file_name)
    metadata["no"] = no if no else _UNKNOWN_NUMERICAL_TAG


def _extract_date(tag, metadata, file_tags, file_name):
    if _extract_numerical_tag(tag, metadata, file_tags, 'year'):
        return
    metadata["year"] = _UNKNOWN_NUMERICAL_TAG


def _extract_other(tag, metadata, file_tags, file_name):
    if _extract_literal_tag(tag, metadata, file_tags):
        return
    metadata[tag.lower()] = _UNKNOWN_LITERAL_TAG


def _extract_literal_tag(tag, metadata, file_tags, alias=None):
    if tag in file_tags:
        value = file_tags[tag]
        if len(value) > 0:
            metadata[alias or tag.lower()] = value[0]
            return True
    return False


def _extract_numerical_tag(tag, metadata, file_tags, alias=None):
    if tag in file_tags:
        value = file_tags[tag]
        if len(value) > 0:
            num = _extract_number(value[0])
            if num:
                metadata[alias or tag.lower()] = num
                return True
    return False


_TAG_EXTRACTORS = {"DATE": _extract_date, "TITLE": _extract_title,
                   "TRACKNUMBER": _extract_tracknumber, "GENRE": _extract_other,
                   "ARTIST": _extract_other, "ALBUM": _extract_other}


def _extract_number(string):
    num = re.findall("([0-9]+)", string)
    if num:
        return int(num[0])
