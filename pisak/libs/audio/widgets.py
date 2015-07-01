"""
Module containing widgets specific to the Pisak audio player application.
"""
from gi.repository import Mx, GObject

from pisak import res
from pisak.libs import widgets, configurator, properties, pager
from pisak.libs.audio import database_manager


class FoldersSource(pager.DataSource):
    """
    Data source that provides tiles representing different folders with music.
    """
    __gtype_name__ = "PisakAudioFoldersSource"

    def __init__(self):
        super().__init__()
        self.data = database_manager.get_all_folders_with_covers()

    def _produce_item(self, data_item):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.style_class = "PisakAudioFolderTile"
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", self.item_handler, data_item[0].id)
        tile.scale_mode = Mx.ImageScaleMode.FIT
        tile.preview_path = data_item[1]
        tile.label_text = data_item[0].name
        return tile


class PlaylistSource(pager.DataSource):
    """
    Data source that provides buttons representing tracks for the playlist.
    """
    __gtype_name__ = "PisakAudioPlaylistSource"

    def __init__(self):
        super().__init__()
        self.data_sets_count = len(
            database_manager.get_all_folders_with_covers())
        self.data_generator = database_manager.get_tracks_from_folder

    def _produce_item(self, data_item):
        button = widgets.Button()
        self._prepare_item(button)
        button.set_style_class("PisakAudioPlaylistButton")
        button.set_label("_ ".join([str(self.data.index(data_item)+1), data_item.title]))
        button.path = data_item.path
        button.info = [data_item.artist, data_item.album]
        button.visual_path = data_item.cover_path
        return button
