"""
Descriptor for PISAK audio app.
"""

from pisak import handlers

import pisak.audio.handlers  # @UnusedImport
from pisak.audio import widgets  # @UnusedImport

def prepare_folders_view(app, window, script, data):
    def _folder_tile_handler(tile, playlist_id):
        window.load_view("audio/playlist", {"playlist_id": playlist_id})

    data_source = script.get_object("data_source")
    data_source.item_handler = _folder_tile_handler
    handlers.button_to_view(window, script, "button_exit")


def prepare_playlist_view(app, window, script, data):
    script.get_object("data_source").data_set_id = data["playlist_id"]
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_return", "audio/main")

audio_app = {
    "app": "audio",
    "type": "clutter",
    "views": [("playlist", prepare_playlist_view),
              ("main", prepare_folders_view)]
}
