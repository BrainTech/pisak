import os.path
from pisak.libs import dirs, media_library


ACCEPTED_TYPES = [
    "image/png", "image/jpeg", "image/x-ms-bmp", "image/gif"]


LIBRARY_DIR = dirs.get_user_dir("pictures")


FAVOURITE_PHOTOS_STORE = os.path.join(dirs.HOME_PISAK_DIR, "favourite_photos.ini")


FAVOURITE_PHOTOS_ALIAS = "ULUBIONE"


_LIBRARY_STORE = {}


def get_library():
    try:
        library = _LIBRARY_STORE[LIBRARY_DIR]
    except KeyError:
        library = media_library.Library(LIBRARY_DIR, ACCEPTED_TYPES, FAVOURITE_PHOTOS_STORE,
                          FAVOURITE_PHOTOS_ALIAS)
        library.include_favs()
        _LIBRARY_STORE[LIBRARY_DIR] = library
    return library
