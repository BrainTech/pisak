"""
ClutterScript paint specific signal handler library.
"""
from gi.repository import Clutter

from pisak import signals, utils


@signals.registered_handler("paint/set_line_color")
def set_line_color(button):
    """
    Set easel line color.

    :param button: color button.
    """
    easel = button.related_object
    easel.line_rgba = utils.convert_color(button.get_background_color())


@signals.registered_handler("paint/set_line_width")
def set_line_width(button):
    """
    Set easel line width.

    :param button: line width button.
    """
    easel = button.related_object
    easel.line_width = int(button.text.split(" ")[0])


@signals.registered_handler("paint/clear_canvas")
def clear_canvas(easel):
    """
    Clear easel canvas.

    :param easel: easel instance.
    """
    easel.clear_canvas()


@signals.registered_handler("paint/save_to_file")
def save_to_file(easel):
    """
    Save easel canvas picture to png file.

    :param easel: easel instance.
    """
    easel.save_to_file()


@signals.registered_handler("paint/new_spot")
def new_spot(easel):
    """
    Localize new drawing spot.

    :param easel: easel instance.
    """
    easel.run_localizer()


@signals.registered_handler("paint/navigate")
def navigate(easel):
    """
    Back to drawing and navigate.

    :param easel: easel instance.
    """
    easel.run_navigator()


@signals.registered_handler("paint/erase")
def erase(easel):
    """
    Erase one step backward.

    :param easel: easel instance.
    """
    easel.erase()
