"""
Module with widgets specific to symboler application.
"""
import os.path

import ezodf
from collections import OrderedDict
from gi.repository import Mx, Clutter, GObject

from pisak import widgets, pager, layout, configurator, \
    dirs, logger
from pisak.res import colors
from pisak.symboler import symbols_manager


_LOG = logger.get_logger(__name__)


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
        Scroll self content forward.
        """
        endmost_symbol = self.get_last_child()
        if endmost_symbol is not None:
            self.scrolled_content_right.append(endmost_symbol)
            self.remove_child(endmost_symbol)
        self._restore_scrolled_content_left()

    def append_many_symbols(self, symbols_list):
        """
        Append many symbols to the entry.
        :param symbols_list: list of symbols identifiers
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
        self._target = None
        self._init = True
        self._sheet_idx = None
        self._ods_idx = None
        self._sheets = {}  # name of a category or 'toc' is a key, list of sheets is a value
        self._current_ods = self.get_toc_ods()
        self._current_type = 'toc'  # 'toc' for table of contents, 'cat' for category
        self._view = 'book'  # whole 'book' or a single 'cat'-egory
        self._order = [('toc', )]
        self._ods_list = [self._current_ods]
        self.custom_topology = True
        self.run()

    def run(self):
        self._length = 100
        self.emit("data-is-ready")

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def get_toc_ods(self):
        return self._open_odf_spreadsheet(
            dirs.get_symbols_spreadsheet('table_of_contents'))

    def get_cat_ods(self, name):
        return self._open_odf_spreadsheet(
            dirs.get_symbols_spreadsheet(name))

    @staticmethod
    def _open_odf_spreadsheet(path):
        try:
            return ezodf.opendoc(path)
        except OSError as exc:
            _LOG.error(exc)

    def _generate_items_custom(self):
        sheet = self._current_ods.sheets[self._sheet_idx]
        self.target_spec["columns"] = sheet.ncols()  # custom number of columns
        self.target_spec["rows"] = sheet.nrows()  # custom number of rows
        items = []
        for row in sheet.rows():
            items_row = []
            for cell in row:
                value = cell.value
                if value:
                    if self._ods_idx == 0:
                        if self._init:
                            self._create_category(value)
                        item = self._produce_toc_item(value)
                    else:
                        item = self._produce_cat_item(value)
                else:
                    item = Clutter.Actor()
                    self._prepare_filler(item)
                self._prepare_item(item)
                items_row.append(item)
            items.append(items_row)
        if self._init:
            self._init = False
        return items

    def next_page(self):
        return self._get_page(1)

    def previous_page(self):
        return _get_page(-1)

    def _load_category(self, category):
        pass

    def _load_main(self):
        pass

    def _create_category(self, name):
        self._ods_list.append(self.get_cat_ods(name))

    def _produce_toc_item(self, value):
        tile = self._produce_item(value)
        tile.connect("clicked", lambda source, category:
                        self._load_category(category), value)
        return tile

    def _produce_cat_item(self, value):
        tile = self._produce_item(value)
        symbol = value + '.png'
        tile.preview_path = dirs.get_symbol_path(value)
        tile.connect("clicked", lambda source, symbol:
                        self.target.append_many_symbols([symbol]), symbol)
        tile.connect("clicked", lambda source: self._load_main())
        return tile

    def _produce_item(self, value):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.style_class = "PisakSymbolerPhotoTileLabel"
        tile.hilite_tool = widgets.Aperture()
        tile.set_background_color(colors.LIGHT_GREY)
        tile.scale_mode = Mx.ImageScaleMode.FIT
        tile.label_text = value
        return tile

    def _prepare_filler(self, filler):
        filler.set_background_color(Clutter.Color.new(255, 255, 255, 255))

    def get_items_custom_next(self):
        """
        Get all items from the next portion. Method compatible with
        custom topology mode of operation.

        :returns: list of items packed into lists
        """
        if self._sheet_idx is None or self._ods_idx is None:
            self._sheet_idx = 0
            self._ods_idx = 0
        else:
            if self._sheet_idx < len(self._current_ods.sheets) - 1:
                self._sheet_idx += 1
            else:
                self._sheet_idx = 0
                if self._ods_idx < len(self._ods_list) - 1:
                    self._ods_idx += 1
                else:
                    self._ods_idx = 0
                self._current_ods = self._ods_list[self._ods_idx]

        print(self._sheet_idx, self._ods_idx)
        return self._generate_items_custom()

    def get_items_custom_previous(self):
        """
        Get all items from the previous portion. Method compatible with
        custom topology mode of operation.

        :returns: list of items packed into lists
        """
        if self._sheet_idx > 0:
            self._sheet_idx -= 1
        else:
            if self._ods_idx > 0:
                self._ods_idx -= 1
            else:
                self._ods_idx = len(self._ods_list) - 1
            self._current_ods = self._ods_list[self._ods_idx]
            self._sheet_idx = len(self._current_ods.sheets) - 1
        return self._generate_items_custom()


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
