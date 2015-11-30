"""
Descriptor for paint app.
"""

from pisak import widgets
import pisak.paint.widgets  # @UnusedImport
import pisak.paint.handlers # @UnusedImport


def prepare_paint_main_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    easel = script.get_object("easel")
    button_start = script.get_object("button_start")
    if button_start is not None and isinstance (button_start, widgets.Button):
        button_start.connect("clicked", easel.clean_up)
        button_start.connect("clicked", lambda *_ : window.stage.destroy())

paint_app = {
    "app": "paint",
    "type": "clutter",
    "views": [("main", prepare_paint_main_view)]
}
