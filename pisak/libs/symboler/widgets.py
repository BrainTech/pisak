"""
Module with widgets specific to symboler application.
"""
import os.path

from gi.repository import Mx, Clutter, GObject

from pisak import res
from pisak.libs import widgets, pager, properties, layout, configurator
from pisak.res import colors
from pisak.libs.symboler import symbols_manager


class Entry(layout.Box, widgets.TileContainer, configurator.Configurable):
    """
    Entry window for typing symbols.
    """
    __gtype_name__ = "PisakSymbolerEntry"
    __gproperties__ = {
        "tile_ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "tile_ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "tile_ratio_spacing": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "tile_preview_ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "tile_preview_ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.text_buffer = []
        self.symbols_buffer = []
        self.scrolled_content_left = []
        self.scrolled_content_right = []
        self.set_x_align(Clutter.ActorAlign.START)
        self.connect("notify::allocation", self._on_allocation_update)
        self.apply_props()

    def _on_allocation_update(self, source, event):
        self.border_x = self.get_abs_allocation_vertices()[1].x

    def _check_content_extent(self, new_symbol):
        endmost_symbol = self.get_last_child()
        # if newly appended symbol would extent over the self allocation area:
        if endmost_symbol is not None:
            if (endmost_symbol.get_abs_allocation_vertices()[1].x +
                self.layout.get_spacing() + new_symbol.get_width()) \
                    > self.border_x:
                if len(self.scrolled_content_right) > 0:
                    while self.scrolled_content_right:
                        self.scroll_content_left()
                self.scroll_content_left()

    def _restore_scrolled_content_left(self):
        if len(self.scrolled_content_left) > 0:
            symbol_to_restore = self.scrolled_content_left.pop()
            self.insert_child_below(symbol_to_restore, None)

    def _restore_scrolled_content_right(self):
        if len(self.scrolled_content_right) > 0:
            symbol_to_restore = self.scrolled_content_right.pop()
            self.insert_child_above(symbol_to_restore, None)

    def _generate_symbol(self, path, text):
        symbol = widgets.PhotoTile()
        symbol.label.set_style_class("PisakSymbolerPhotoTileLabel")
        symbol.label_text = text
        symbol.set_y_expand(True)
        symbol.ratio_width = self.tile_ratio_width
        symbol.ratio_spacing = self.tile_ratio_spacing
        symbol.preview_ratio_width = self.tile_preview_ratio_width
        symbol.preview_ratio_height = self.tile_preview_ratio_height
        symbol.scale_mode = Mx.ImageScaleMode.FIT
        symbol.preview_path = os.path.join(symbols_manager.SYMBOLS_DIR, path)
        return symbol

    def scroll_content_left(self):
        """
        Scroll self content backward.
        """
        first_symbol = self.get_child_at_index(0)
        if first_symbol is not None:
            self.scrolled_content_left.append(first_symbol)
            self.remove_child(first_symbol)
        self._restore_scrolled_content_right()

    def scroll_content_right(self):
        """
        Scroll self content foreward.
        """
        endmost_symbol = self.get_last_child()
        if endmost_symbol is not None:
            self.scrolled_content_right.append(endmost_symbol)
            self.remove_child(endmost_symbol)
        self._restore_scrolled_content_left()

    def append_many_symbols(self, symbols_list):
        """
        Append many symbols to the entry.
        :param symbols_list: list of symbols identificators       
        """
        for item in symbols_list:
            text = symbols_manager.get_symbol(item)
            self.symbols_buffer.append(item)
            self.text_buffer.append(text)
            symbol = self._generate_symbol(item, text)
            self._check_content_extent(symbol)
            self.insert_child_above(symbol, None)

    def delete_symbol(self):
        """
        Delete the last symbol from the entry.
        """
        if len(self.scrolled_content_right) > 0:
            while self.scrolled_content_right:
                self.scroll_content_left()
        endmost_symbol = self.get_last_child()
        if endmost_symbol is not None:
            self.remove_child(endmost_symbol)
            if len(self.text_buffer) > 0:
                self.text_buffer.pop()
            if len(self.symbols_buffer) > 0:
                self.symbols_buffer.pop()
        self._restore_scrolled_content_left()

    def get_text(self):
        """
        Return string containing current text buffer.
        """
        return " ".join(self.text_buffer)

    def clear_all(self):
        """
        Clear the entry, delete all symbols.
        """
        self.text_buffer = []
        self.symbols_buffer = []
        self.remove_all_children()


class TilesSource(pager.DataSource):
    """
    Data source generating tiles with symbols.
    """
    __gtype_name__ = "PisakSymbolerTilesSource"
    __gproperties__ = {
        "target": (
            Entry.__gtype__,
            "symbol inserting target",
            "id of entry to insert symbols",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        data = symbols_manager.get_symbols_from_spreadsheet()
        if data:
            self.custom_topology = True
        else:
            data = symbols_manager.get_all_symbols()
        self.data = data

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def _produce_item(self, data_item):
        item, text = data_item
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.style_class = "PisakSymbolerPhotoTileLabel"
        tile.label_text = text
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", lambda source, item:
                        self.target.append_many_symbols([item]), item)
        tile.set_background_color(colors.LIGHT_GREY)
        tile.scale_mode = Mx.ImageScaleMode.FIT
        tile.preview_path = os.path.join(symbols_manager.SYMBOLS_DIR, item)
        return tile

    def _prepare_filler(self, filler):
        filler.set_background_color(Clutter.Color.new(255, 255, 255, 255))


class PopUp(widgets.DialogWindow):
    """
    Dialog window for purposes of saving and loading symbols entries.
    """
    __gtype_name__ = "PisakSymbolerPopUp"

    def __init__(self):
        super().__init__()
        # field for callback function executing the proper saving operation
        self.overwrite_entry = None
        self.apply_props()

    def _generate_content(self, entries=None):
        if entries:
            for idx, name in enumerate(entries):
                if idx % self.column_count == 0:
                    row = layout.Box()
                    row.spacing = self.spacing
                    self.space.add_child(row)
                button = widgets.Button()
                button.set_style_class("PisakSymbolerButton")
                button.set_label(name)
                button.ratio_width = self.tile_ratio_width
                button.ratio_height = self.tile_ratio_height
                button.connect("clicked", self._on_select, name, entries[name])
                row.add_child(button)
        row = layout.Box()
        row.spacing = self.spacing
        self.space.add_child(row)
        button = widgets.Button()
        row.add_child(button)
        button.set_style_class("PisakSymbolerButton")
        button.ratio_width = self.tile_ratio_width
        button.ratio_height = self.tile_ratio_height
        button.connect("clicked", self._close)
        if entries:
            button.set_label(self.exit_button_label)
        else:
            button.set_label(self.continue_button_label)

    def _on_select(self, button, name, entry):
        if self.mode == "save":
            self.overwrite_entry(name, self.target.symbols_buffer)
        elif self.mode == "load":
            self.target.clear_all()
            self.target.append_many_symbols(entry)
        self._close(None)
