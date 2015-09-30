


def __init__(self):
    self._sheets = []


def load_page():
    rows, cols = sheet.nrows(), sheet.ncols()  # number of rows and columns on the page
    self.view.display_grid(rows, cols)
    for row_idx, row in enumerate(sheet.rows()):
        for col_idx, cell in enumerate(row):
            self.view.display_item(col_idx, row_idx, self.parse_cell(cell))







class DataSource:


    def __init__(self):
        super().__
        self._sheet_idx = 0
        self._sheets = []
        self._current_ods = self.get_toc_ods()
        self._current_sheet = self._current_ods.sheets[0]
        self._current_type = 'toc'  # 'toc' for table of contents, 'cat' for category
        self._order = [('toc', )]
        self._categories = {}
        self._length = 10
        self.run()


    def run(self):
        self.emit("data-is-ready")

    def get_toc_ods(self):
        return self._open_odf_spreadsheet(
            dirs.get_symbols_spreadsheet('table_of_contents'))

    def get_cat_ods(self, name):
        return self._open_odf_spreadsheet(
            dirs.get_symbols_spreadsheet(name))

    def _open_odf_spreadsheet(path):
        try:
            return ezodf.opendoc(path)
        except OSError as exc:
            _LOG.error(exc)

    def _generate_items_custom(self, sheet):
        self.target_spec["columns"] = sheet.ncols()  # custom number of columns
        self.target_spec["rows"] = sheet.nrows()  # custom number of rows
        items = []
        for row in sheet.rows():
            items_row = []
            for cell in row:
                value = cell.value
                if value:
                    if self._current_type == 'toc':
                        self._create_category(value)
                        item = self._produce_toc_item(value)
                    elif self._current_type == 'cat':
                        item = self._produce_cat_item(value)
                else:
                    item = Clutter.Actor()
                    self._prepare_filler(item)
                self._prepare_item(item)
                items_row.append(item)
            items.append(items_row)
        return items

    def next_page(self):
        return self._get_page(1)

    def previous_page(self):
        return _get_page(-1)

    def _load_category(self, category):
        self.reload(pisak.app.box['categories_dict'][category])

    def _load_main(self):
        self.reload(pisak.app.box['book'])

    def _create_category(self, name):
        if name not in self._categories:
          self._categories[name] =  self._get_cat_ods(name)

    def _produce_toc_item(self, value):
        tile = self._produce_item(value)
        tile.connect("clicked", lambda source, category:
                        self._load_category(category), value)
        return tile

    def _produce_cat_item(self, value):
        tile = self._produce_item(value)
        symbol = value + '.png'
        tile.preview_path = dirs.get_symbol_path(symbol)
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







def put_placeholder(coords):



def display_item(coords, item):
    # replace actor


def display_grid(rows, cols):



def parse_toc_cell(cell):
    value = cell.value
    if value:

        self._sheets.append(cs)

    else:


def parse_category_cell(cell):



def next_page():


def previous_page():

