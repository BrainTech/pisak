from pisak import signals
from pisak.movie import model


@signals.registered_handler("movie/toggle_fullscreen")
def toggle_fullscreen(movie_widget):
    """
    Turn on or turn off the fullscreen mode.
    :param movie_widget: pisak movie widget
    """
    movie_widget.toggle_fullscreen()


@signals.registered_handler("movie/add_or_remove_from_favs")
def add_or_remove_from_favs(playback):
    """
    Add or remove the currently displayed movie from the favourites.

    :param playback: videoplayback with movie to be marked as favourite
    """
    path = playback.filename
    lib = model.get_library()
    if lib.is_in_favourites(path):
        lib.remove_item_from_favourites(path)
    else:
        lib.add_item_to_favourites(path)
