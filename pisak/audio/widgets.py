"""
Module containing widgets specific to the Pisak audio player application.
"""
from gi.repository import Mx, GObject

from pisak import res, widgets, configurator, properties, pager
from pisak.audio import db_manager


class FoldersSource(pager.DataSource):
    """
    Data source that provides tiles representing different folders with music.
    """
    __gtype_name__ = "PisakAudioFoldersSource"

    def __init__(self):
        super().__init__()
        self.data = db_manager.DBConnector().get_all_folders()

    def _produce_item(self, folder):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.style_class = "PisakAudioFolderTile"
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", self.item_handler, folder['id'])
        tile.scale_mode = Mx.ImageScaleMode.FIT
        tile.preview_path = folder['cover_path']
        tile.label_text = folder['name']
        return tile


class PlaylistSource(pager.DataSource):
    """
    Data source that provides buttons representing tracks for the playlist.
    """
    __gtype_name__ = "PisakAudioPlaylistSource"

    def __init__(self):
        super().__init__()
        db = db_manager.DBConnector()
        self.data_sets_ids_list = db.get_folders_ids()
        self.data_sets_count = len(self.data_sets_ids_list)
        self.data_generator = db.get_tracks_from_folder

    def _produce_item(self, track):
        button = widgets.Button()
        self._prepare_item(button)
        button.set_style_class("PisakAudioPlaylistButton")
        button.set_label("_ ".join([str(self.data.index(track)+1), track['title']]))
        button.path = track['path']
        button.info = [track['artist'], track['album']]
        button.visual_path = track['cover_path']
        return button
