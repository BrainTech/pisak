"""
Photo library management center.
"""
import os.path
from pisak import dirs, media_library


ACCEPTED_TYPES = [
    ".jpg", ".jpeg", ".png", ".bmp", ".gif"
]


LIBRARY_DIR = dirs.get_user_dir("pictures")


FAVOURITE_PHOTOS_STORE = os.path.join(dirs.HOME_PISAK_FAVOURITES, "favourite_photos.ini")


FAVOURITE_PHOTOS_ALIAS = "ULUBIONE"


_LIBRARY_STORE = {}


def get_library():
    """
    Retrieve the photo library. Library is loaded just once and then is stored
    as a module-level variable.

    :return: library.
    """
    try:
        library = _LIBRARY_STORE[LIBRARY_DIR]
    except KeyError:
        library = media_library.Library(LIBRARY_DIR, ACCEPTED_TYPES, FAVOURITE_PHOTOS_STORE,
                          FAVOURITE_PHOTOS_ALIAS)
        library.include_favs()
        _LIBRARY_STORE[LIBRARY_DIR] = library
    return library
