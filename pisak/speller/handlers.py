"""
Speller application specific handlers.
"""
import subprocess
import os

import pisak
from pisak import signals, sound_effects
from pisak.speller import widgets, documents_manager


@signals.registered_handler("speller/scroll_up")
def scroll_up(text_box):
    """
    Scroll the text field up.

    :param text_box: text box.
    """
    text_box.scroll_up()


@signals.registered_handler("speller/scroll_down")
def scroll_down(text_box):
    """
    Scroll the text field down.

    :param text_box: text box.
    """
    text_box.scroll_down()


@signals.registered_handler("speller/undo")
def undo(text_box):
    """
    Undo the last operation applied to a text box.

    :param text_box: undoable text box.
    """
    text_box.revert_operation()


@signals.registered_handler("speller/nav_right")
def nav_right(text_box):
    """
    Move text cursor forward for one position.

    :param text_box: text box.
    """
    text_box.move_cursor_forward()


@signals.registered_handler("speller/nav_left")
def nav_left(text_box):
    """
    Move text cursor backward for one position.

    :param text_box: text box.
    """
    text_box.move_cursor_backward()


@signals.registered_handler("speller/nav_down")
def nav_down(text_box):
    """
    Move text cursor one line down.

    :param text_box: text box.
    """
    text_box.move_line_down()


@signals.registered_handler("speller/nav_up")
def nav_up(text_box):
    """
    Move text cursor one line up.

    :param text_box: text box.
    """
    text_box.move_line_up()


@signals.registered_handler("speller/nav_word_backward")
def nav_word_backward(text_box):
    """
    Move text cursor backward skipping one word.

    :param text_box: text box.
    """
    text_box.move_word_backward()


@signals.registered_handler("speller/nav_word_forward")
def nav_word_forward(text_box):
    """
    Move text cursor forward skipping one word.

    :param text_box: text box.
    """
    text_box.move_word_forward()


@signals.registered_handler("speller/save")
def save(pop_up):
    """
    Save the current text buffer content to a text file.
    Open a dialog window.

    :param pop_up: dialog window.
    """
    file_overwrite_message = "WYBIERZ PLIK DO NADPISANIA"
    empty_text_box_message = "BRAK TEKSTU DO ZAPISANIA"
    save_success_message = "POMYŚLNIE ZAPISANO PLIK:"
    file_name_base = "plik nr "
    files_limit = 9
    pop_up.mode = "save"
    text_box = pop_up.target
    files = documents_manager.get_all_documents()
    text = text_box.get_text()
    if text:
        if len(files) < files_limit:
            name = file_name_base + str(len(files)+1)
            file_path = documents_manager.generate_new_path()
            documents_manager.add_document(name, file_path)
            with open(file_path, "w") as file:
                file.write(text)
            message = save_success_message + "\n\n" + '"' + name + '"'
            pop_up.on_screen(message)
        else:
            pop_up.on_screen(file_overwrite_message, files)
    else:
        pop_up.on_screen(empty_text_box_message)


@signals.registered_handler("speller/load")
def load(pop_up):
    """
    Load one of the previously saved text files. Put the text
    inside the text box.
    Open a dialog window.

    :param pop_up: dialog window.
    """
    files_present_message = "WYBIERZ PLIK"
    no_files_present_message = "BRAK PLIKÓW DO WCZYTANIA"
    pop_up.mode = "load"
    files = documents_manager.get_all_documents()
    if files:
        pop_up.on_screen(files_present_message, files)
    else:
        pop_up.on_screen(no_files_present_message)


@signals.registered_handler("speller/print")
def print_doc(text_box):
    """
    Print text from the text buffer.

    :param text_box: text box.
    """
    raise NotImplementedError


@signals.registered_handler("speller/send")
def send(text_box):
    """
    Send text from the text buffer by means of some other application.

    :param text_box: text box.
    """
    raise NotImplementedError


@signals.registered_handler("speller/new_document")
def new_document(text_box):
    """
    Remove the whole text from the text buffer and clear the text box.

    :param text_box: text box.
    """
    text_box.clear_all()


@signals.registered_handler("speller/text_to_speech")
def text_to_speech(text_box):
    """
    Read the text loud.

    :param text_box: text box.
    """
    text = text_box.get_text()
    if text:
        synth = sound_effects.Synthesizer(text)
        if pisak.app.window.input_group.middleware == "scanning":
            synth.read_and_call(pisak.app.window.pending_group.start_cycle)
        else:
            synth.read()


@signals.registered_handler("speller/backspace")
def backspace(text_box):
    """
    Delete the one last character from the text buffer.

    :param text_box: text box.
    """
    text_box.delete_char()


@signals.registered_handler("speller/space")
def space(text_box):
    """
    Insert space in the end of the text buffer.

    :param text_box: text box.
    """
    text_box.type_text(" ")

@signals.registered_handler("speller/enter")
def enter(text_box):
    """
    Insert enter in the end of the text buffer.

    :param text_box: text box.
    """
    text_box.move_to_new_line()


@signals.registered_handler("speller/new_line")
def new_line(text_box):
    """
    Begin a new line of text.

    :param text_box: text box.
    """
    text_box.move_to_new_line()


@signals.registered_handler("speller/previous_chars")
def previous_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the previously displayed ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.undo_label()
        try:
            keyboard_item.disconnect_by_func(previous_chars)
        except TypeError:
            return None
    else:
        for sub_item in keyboard_item.get_children():
            previous_chars(sub_item)


@signals.registered_handler("speller/default_chars")
def default_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the default ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_default_label()
    else:
        for sub_item in keyboard_item.get_children():
            default_chars(sub_item)


@signals.registered_handler("speller/special1_chars")
def special1_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the special ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_special_label("special1")
        undo = widgets.Key.set_swap_special_label
        if undo not in keyboard_item.undo_chain:
            keyboard_item.undo_chain.append(undo)
    else:
        for sub_item in keyboard_item.get_children():
            special1_chars(sub_item)

@signals.registered_handler("speller/special2_chars")
def special2_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the extra ones (including emoticons).

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_special_label("special2")
        undo = widgets.Key.set_swap_special_label
        if undo not in keyboard_item.undo_chain:
            keyboard_item.undo_chain.append(undo)
    else:
        for sub_item in keyboard_item.get_children():
            special2_chars(sub_item)

@signals.registered_handler("speller/altgr_chars")
def altgr_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the ones specified by altgr property.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_altgr_label()
        undo = widgets.Key.set_swap_altgr_label
        if undo not in keyboard_item.undo_chain:
            keyboard_item.undo_chain.append(undo)
    else:
        for sub_item in keyboard_item.get_children():
            altgr_chars(sub_item)


@signals.registered_handler("speller/caps_chars")
def caps_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the upper cased ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_caps_label()
        undo = widgets.Key.set_lower_label
        if undo not in keyboard_item.undo_chain:
            keyboard_item.undo_chain.append(undo)
    else:
        for sub_item in keyboard_item.get_children():
            caps_chars(sub_item)


@signals.registered_handler("speller/lower_chars")
def lower_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the lower cased ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_lower_label()
        undo = widgets.Key.set_caps_label
        if undo not in keyboard_item.undo_chain:
            keyboard_item.undo_chain.append(undo)
    else:
        for sub_item in keyboard_item.get_children():
            lower_chars(sub_item)


@signals.registered_handler("speller/swap_special1_chars")
def swap_special1_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the special or default ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_swap_special_label("special1")
        keyboard_item.undo_chain.append(widgets.Key.set_swap_special_label)
    else:
        for sub_item in keyboard_item.get_children():
            swap_special1_chars(sub_item)

@signals.registered_handler("speller/swap_special2_chars")
def swap_special2_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the special or default ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_swap_special_label("special2")
        keyboard_item.undo_chain.append(widgets.Key.set_swap_special_label)
    else:
        for sub_item in keyboard_item.get_children():
            swap_special2_chars(sub_item)

@signals.registered_handler("speller/swap_altgr_chars")
def swap_altgr_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the ones specified by
    altgr property or to the default ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_swap_altgr_label()
        keyboard_item.undo_chain.append(widgets.Key.set_swap_altgr_label)
    else:
        for sub_item in keyboard_item.get_children():
            swap_altgr_chars(sub_item)


@signals.registered_handler("speller/swap_caps_chars")
def swap_caps_chars(keyboard_item):
    """
    Change chars on the keyboard keys to the upper or lower cased ones.

    :param keyboard_item: some possibly nested keyboard item.
    """
    if isinstance(keyboard_item, widgets.Key):
        keyboard_item.set_swap_caps_label()
        keyboard_item.undo_chain.append(widgets.Key.set_swap_caps_label)
    else:
        for sub_item in keyboard_item.get_children():
            swap_caps_chars(sub_item)


@signals.registered_handler("speller/lower_chars_on_select")
def lower_chars_on_select(keyboard_panel):
    """
    Automatically change chars on the keyboard keys to the lower cased ones
    after typing one of the characters.

    :param keyboard_item: container with pisak key instances inside.
    """
    _previous_chars_on_select(keyboard_panel, keyboard_panel, widgets.Key.set_lower_label)


@signals.registered_handler("speller/caps_chars_on_select")
def caps_chars_on_select(keyboard_panel):
    """
    Automatically change chars on the keyboard keys to the upper cased ones
    after typing one of the characters.

    :param keyboard_item: container with pisak key instances inside.
    """
    _previous_chars_on_select(keyboard_panel, keyboard_panel, widgets.Key.set_caps_label)


@signals.registered_handler("speller/swap_caps_chars_on_select")
def swap_caps_chars_on_select(keyboard_panel):
    """
    Automatically change chars on the keyboard keys to the lower or upper
    cased ones after typing one of the characters.

    :param keyboard_item: container with pisak key instances inside.
    """
    _previous_chars_on_select(keyboard_panel, keyboard_panel, widgets.Key.set_swap_caps_label)


@signals.registered_handler("speller/swap_altgr_chars_on_select")
def swap_altgr_chars_on_select(keyboard_panel):
    """
    Automatically change chars on the keyboard keys to the ones specified by
    altgr property or to the default ones after typing one of the characters.

    :param keyboard_item: container with pisak key instances inside.
    """
    _previous_chars_on_select(keyboard_panel, keyboard_panel, widgets.Key.set_swap_altgr_label)


@signals.registered_handler("speller/swap_special_chars_on_select")
def swap_special_chars_on_select(keyboard_panel):
    """
    Automatically change chars on the keyboard keys to the special or default
    ones after typing one of the characters.

    :param keyboard_item: container with pisak key instances inside.
    """
    _previous_chars_on_select(keyboard_panel, keyboard_panel, widgets.Key.set_swap_special_label)


@signals.registered_handler("speller/unset_toggled_state_on_select")
def unset_toggled_state_on_select(button):
    """
    Automatically unset toggled state of the button after selecting one
    of the keyboard keys.

    :param button: speller button instance.
    """
    keyboard_panel = button.related_object
    key_bag = []
    _find_and_get_keys(keyboard_panel, key_bag)
    for key in key_bag:
        try:
            key.disconnect_by_func(unset_toggled_state)
        except TypeError:
            pass
        key.connect_object("clicked", unset_toggled_state, button)


@signals.registered_handler("speller/unset_toggled_state")
def unset_toggled_state(button):
    """
    Unset toggled state of the button.

    :param button: speller button instance.
    """
    if button.get_toggled():
        button.set_toggled(False)
    try:
        keyboard_panel = button.related_object
        key_bag = []
        _find_and_get_keys(keyboard_panel, key_bag)
        for key in key_bag:
            try:
                key.disconnect_by_func(unset_toggled_state)
            except TypeError:
                pass
    except AttributeError:
        pass


@signals.registered_handler("speller/set_toggled_state")
def set_toggled_state(button):
    """
    Set toggled state of the button.

    :param button: speller button instance.
    """
    if not button.get_toggled():
        button.set_toggled(True)


@signals.registered_handler("speller/switch_toggled_state")
def switch_toggled_state(button):
    """
    Set or unset toggled state of the button.

    :param button: speller button instance.
    """
    if button.get_toggled():
        button.set_toggled(False)
    else:
        button.set_toggled(True)


def _previous_chars_on_select(keyboard_item, keyboard_panel, allowed_undo):
    if isinstance(keyboard_item, widgets.Key):
        try:
            keyboard_item.disconnect_by_func(previous_chars)
        except TypeError:
            pass
        keyboard_item.connect_object("clicked", previous_chars, keyboard_panel)
        keyboard_item.allowed_undos.add(allowed_undo)
    else:
        for sub_item in keyboard_item.get_children():
            _previous_chars_on_select(sub_item, keyboard_panel, allowed_undo)


def _find_and_get_keys(keyboard_item, key_bag):
    if isinstance(keyboard_item, widgets.Key):
        key_bag.append(keyboard_item)
    else:
        for sub_item in keyboard_item.get_children():
            _find_and_get_keys(sub_item, key_bag)
