import subprocess

from pisak import signals
from pisak.symboler import symbols_manager


@signals.registered_handler("symboler/save")
def save(pop_up):
    """
    Save the current symbols buffer.
    Open a dialog window.

    :param pop_up: dialog window
    """
    def do_save(entry, symbols):
        symbols_manager.save_entry(entry, symbols)

    entry_overwrite_message = "WYBIERZ PLIK DO NADPISANIA"
    empty_entry_box_message = "BRAK SYMBOLI DO ZAPISANIA"
    save_success_message = "POMYŚLNIE ZAPISANO PLIK:"
    entry_name_base = "plik nr "
    entries_limit = 9
    pop_up.mode = "save"
    entry_box = pop_up.target
    entries = symbols_manager.get_saved_entries()
    symbols = entry_box.symbols_buffer
    if symbols:
        if len(entries) < entries_limit:
            name = entry_name_base + str(len(entries)+1)
            do_save(name, symbols)
            message = save_success_message + "\n\n" + '"' + name + '"'
            pop_up.on_screen(message)
        else:
            pop_up.on_screen(entry_overwrite_message, entries)
            pop_up.overwrite_entry = do_save
    else:
        pop_up.on_screen(empty_entry_box_message)


@signals.registered_handler("symboler/load")
def load(pop_up):
    """
    Load one of the previously saved symbols chains. Put the symbols
    inside the entry.
    Open a dialog window.

    :param pop_up: dialog window
    """
    entries_present_message = "WYBIERZ PLIK"
    no_entries_present_message = "BRAK PLIKÓW DO WCZYTANIA"
    pop_up.mode = "load"
    entries = symbols_manager.get_saved_entries()
    if entries:
        pop_up.on_screen(entries_present_message, entries)
    else:
        pop_up.on_screen(no_entries_present_message)


@signals.registered_handler("symboler/text_to_speech")
def text_to_speech(entry):
    """
    Read the text loud.
    :param entry: symbols entry
    """
    text = entry.get_text()
    if text:
        subprocess.Popen(["milena_say", text])


@signals.registered_handler("symboler/backspace")
def backspace(entry):
    """
    Delete the last symbol from the entry.
    :param entry: symbols entry
    """
    entry.delete_symbol()


@signals.registered_handler("symboler/clear_all")
def clear_all(entry):
    """
    Clear the whole entry.
    :param entry: symbols entry
    """
    text = entry.clear_all()


@signals.registered_handler("symboler/scroll_left")
def scroll_left(entry):
    """
    Scroll the entry content left.
    :param entry: symbols entry
    """
    if len(entry.scrolled_content_right) > 0:
        entry.scroll_content_left()


@signals.registered_handler("symboler/scroll_right")
def scroll_right(entry):
    """
    Scroll the entry content right.
    :param entry: symbols entry
    """
    if len(entry.scrolled_content_left) > 0:
        entry.scroll_content_right()


