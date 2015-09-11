import os
import configobj

import ezodf

from pisak import res, logger, dirs, exceptions


_LOG = logger.get_logger(__name__)


SYMBOLS_DIR = res.get("symbols")


def create_model():
    """
    Extract information about all files with symbols from the default
    symbols directory. Every symbol will be represented as a list consisting of
    a path to the symbol file and a text assigned to it.
    Create or update file with their specification and hierarchy.
    Any changes applied previously to the records in the spec
    file will not be overwritten.
    """
    model = configobj.ConfigObj(dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')
    items = model.keys()
    if "ALL" not in items:
        model["ALL"] = {}
    for current, _subdirs, files in os.walk(SYMBOLS_DIR):
        if current is not SYMBOLS_DIR:
            category = os.path.split(current)[-1]
            if category not in items:
                model[category] = {}
        else:
            category = None
        for file in files:
            relative_path = os.path.join(current.replace(SYMBOLS_DIR, ""), file)
            text = os.path.splitext(file)[0].replace("_", " ")
            model["ALL"][relative_path] = text
            if category:
                model[category][relative_path] = text
    model.write()


def assign_text_to_symbol(symbol, text):
    """
    Assign the text to the given symbol.

    :param symbol: symbol identificator
    :param text: text to be assigned to the symbol
    """
    model = configobj.ConfigObj(dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')
    for section in model.keys():
        if symbol in model[section].keys():
            model[section][symbol] = text
    model.write()


def add_symbol_to_category(symbol, category):
    """
    Add a symbol to the given category.

    :param symbol: symbol indentificator
    :param category: name of the category
    """
    model = configobj.ConfigObj(dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')
    model[category][symbol] = model["ALL"][symbol]
    model.write()


def get_symbol(symbol):
    """
    Get symbol specified by the given id.

    :param symbol: symbol identificator
    """
    model = configobj.ConfigObj(dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')
    if symbol in model["ALL"].keys():
        return model["ALL"][symbol]


def get_symbols(symbols_list):
    """
    Get all symbols specified in the given list.

    :param symbols_list: list with symbols identificators
    """
    symbols = []
    model = configobj.ConfigObj(dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')
    all_symbols = model["ALL"].keys()
    for item in symbols_list:
        if item in all_symbols:
            symbols.append(model["ALL"][item])
    return symbols


def _open_odf_spreadsheet(path):
    try:
        return ezodf.opendoc(path)
    except OSError as exc:
        _LOG.error(exc)
        raise exceptions.PisakException(exc)


def get_symbols_from_spreadsheet(spreadsheet=dirs.HOME_SYMBOLS_SPREADSHEET):
    """
    Parse the spreadsheet and get symbols topology description.
    Order of iteration is as follows- first sheets, then rows and finally
    columns. For each cell there is a list created that contains two elements-
    symbol name with extension and bare symbol name (which is a
    temporary solution).

    :returns: topology of symbols pages, list of lists, each for one page,
    of lists, each for one row, of symbols or Nones, for an empty fields.
    """
    file = _open_odf_spreadsheet(spreadsheet)
    return [[[[sheet[row, col].value + ".png", sheet[row, col].value]
                  if isinstance(sheet[row, col].value, str) and
                  get_symbol(sheet[row, col].value + ".png") else None
                      for col in range(sheet.ncols())]
                         for row in range(sheet.nrows())]
                            for sheet in file.sheets]


def get_toc_spreadsheet():
    """
    Get path to a spreadsheet with the table of contents.

    :return: path to the spreadsheet.
    """
    return dirs.get_symbols_spreadsheet('table_of_contents')


def get_category_spreadsheet(name):
    """
    Get path to a spreadsheet with symbols from the given category.

    :param name: name of the category.

    :return: path to the spreadsheet.
    """
    return dirs.get_symbols_spreadsheet(name)


def parse_from_spreadsheets():
    """
    Parse table of contents and all the categories and store them
    inside a single dictionary.

    :return: dictionary with the symbols from various categories;
    table of contents structure and all the categories structures together
    or None if no table of contents found.
    """
    toc_path = get_toc_spreadsheet()
    try:
        file = _open_odf_spreadsheet(toc_path)
    except exceptions.PisakException as exc:
        return

    symbols = {}
    toc = []
    flat = []
    for sheet in file.sheets:
        page = []
        toc.append(page)
        for r in range(sheet.nrows()):
            row = []
            page.append(row)
            for c in range(sheet.ncols()):
                val = sheet[r, c].value
                if isinstance(val, str):
                    category = get_symbols_from_spreadsheet(
                        get_category_spreadsheet(val))
                    symbols[val] = category
                    flat.extend(category)
                    row.append(val)
                else:
                    row.append(None)
    return symbols, toc, toc + flat


def get_all_symbols():
    """
    Get all avalaible symbols.
    """
    return _get_symbols_from_section("ALL")


def get_symbols_from_category(category):
    """
    Get all symbols from the given directory.

    :param category: category of symbols
    """
    return _get_symbols_from_section(category)


def _get_symbols_from_section(section):
    return list(configobj.ConfigObj(
        dirs.HOME_SYMBOLS_MODEL, encoding='UTF8')[section].items())


def get_saved_entries():
    """
    Get all previously saved symbols entries.
    """
    return configobj.ConfigObj(dirs.HOME_SYMBOLS_ENTRY, encoding='UTF8')


def save_entry(name, entry):
    """
    Save the given entry.

    :param entry: chain of symbols to be saved
    :param title: title of the new entry
    """
    entries = configobj.ConfigObj(dirs.HOME_SYMBOLS_ENTRY, encoding='UTF8')
    entries[name] = entry
    entries.write()
