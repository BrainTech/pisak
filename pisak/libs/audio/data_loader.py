import os
import re
import time
import configobj
from collections import defaultdict

import taglib

from pisak import res
from pisak.libs import dirs, utils
from pisak.libs.audio import database_manager


_LIBRARY_DIR = dirs.get_user_dir("music")

_COVER_EXTENSIONS = [
    "jpg", "jpeg", "png", "bmp"]

_LOAD_TRACKER = os.path.join(dirs.HOME_PISAK_DIR, "music_load_tracker.ini")

_FAKE_COVER_NAME = "fake_cover.png"

_UNKNOW_LITERAL_TAG = "nieznane"

_UNKNOW_NUMERICAL_TAG = 0


def load_all():
    """
    Load informations about the music library in the filesystem and
    insert them to the database.
    """
    database_manager.collect_garbage()
    folder_tree = defaultdict(list)
    last_load_time = _get_last_load_time()
    for current, subdirs, files in os.walk(_LIBRARY_DIR):
        if current is _LIBRARY_DIR:
            first_level_folders = list(map(lambda subdir:
                            os.path.join(current, subdir), subdirs))
        if os.path.getmtime(current) > last_load_time:
            folder_name = os.path.split(current)[-1].lower()
            cover_path = utils.find_folder_image(files, folder_name, current,
                                          _COVER_EXTENSIONS)
            if not cover_path:
                cover_path = os.path.join(current, _FAKE_COVER_NAME)
                utils.produce_identicon(current, save_path=cover_path)
            for file_name in files:
                path = os.path.join(current, file_name)
                meta = _get_metadata(path, file_name)
                if meta:
                    if current in first_level_folders + [_LIBRARY_DIR]:
                        folder_tree[folder_name].append([meta["TITLE"],
                                    path, meta["TRACKNUMBER"], meta["DATE"],
                                    cover_path, meta["ALBUM"], meta["ARTIST"],
                                    meta["GENRE"]])
    database_manager.insert_folder_tree(folder_tree)
    _update_last_load_time(time.time())


def _get_last_load_time():
    if not os.path.isfile(_LOAD_TRACKER):
        return 0
    else:
        return float(configobj.ConfigObj(_LOAD_TRACKER, encoding='UTF8').get(
            "last_load_time"))


def _update_last_load_time(time):
    conf = configobj.ConfigObj(_LOAD_TRACKER, encoding='UTF8')
    conf["last_load_time"] = time
    conf.write()


def _get_metadata(path, file_name):
    try:
        file_tags = taglib.File(path).tags
    except OSError:
        print("Could not read file: {}".format(path))
        return False
    metadata = dict()
    for tag, func in _TAG_EXTRACTORS.items():
        func(tag, metadata, file_tags, file_name)
    return metadata


def _extract_title(tag, metadata, file_tags, file_name):
    if _extract_literal_tag(tag, metadata, file_tags):
        return
    metadata["TITLE"] = os.path.splitext(file_name)[0]


def _extract_tracknumber(tag, metadata, file_tags, file_name):
    if _extract_numerical_tag(tag, metadata, file_tags):
        return
    no = _extract_number(file_name)
    metadata["TRACKNUMBER"] = no if no else _UNKNOW_NUMERICAL_TAG


def _extract_date(tag, metadata, file_tags, file_name):
    if _extract_numerical_tag(tag, metadata, file_tags):
        return
    metadata["DATE"] = _UNKNOW_NUMERICAL_TAG


def _extract_other(tag, metadata, file_tags, file_name):
    if _extract_literal_tag(tag, metadata, file_tags):
        return
    metadata[tag] = _UNKNOW_LITERAL_TAG


def _extract_literal_tag(tag, metadata, file_tags):
    if tag in file_tags.keys():
        value = file_tags[tag]
        if len(value) > 0:
            metadata[tag] = value[0]
            return True
    return False


def _extract_numerical_tag(tag, metadata, file_tags):
    if tag in file_tags.keys():
        value = file_tags[tag]
        if len(value) > 0:
            num = _extract_number(value[0])
            if num:
                metadata[tag] = num
                return True
    return False


_TAG_EXTRACTORS = {"DATE": _extract_date, "TITLE": _extract_title,
                   "TRACKNUMBER": _extract_tracknumber, "GENRE": _extract_other,
                   "ARTIST": _extract_other, "ALBUM": _extract_other}


def _extract_number(string):
    num = re.findall("([0-9]+)", string)
    if num:
        return int(num[0])
