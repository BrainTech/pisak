"""
Desriptor for the movie player.
"""

from pisak import handlers
from pisak.movie import widgets, model
import pisak.movie.handlers  # @UnusedImport


def prepare_flat_view(app, window, script, data):
    def movie_tile_handler(tile, movie_id):
        window.load_view(
            "movie/player", {"movie_id": movie_id})

    data_source = script.get_object("library_data")
    data_source.item_handler = movie_tile_handler
    handlers.button_to_view(window, script, "button_start")
    data_source.emit('data-is-ready')


def prepare_player_view(app, window, script, data):
    movie_id = data.get("movie_id")
    library = model.get_library()
    movie = library.get_item_by_id(movie_id)
    movie_path = movie.path
    playback = script.get_object("playback")
    playback.filename = movie_path
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_library", "movie/main")

movie_app = {
    "app": "movie",
    "type": "clutter",
    "views": [("player", prepare_player_view),
              ("main", prepare_flat_view)]
}
