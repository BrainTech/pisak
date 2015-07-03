"""
Paint application main module
"""
import pisak
from pisak import app_manager
from pisak.libs import widgets
import pisak.libs.paint.widgets  # @UnusedImport
from pisak.libs.paint import handlers # @UnusedImport


def prepare_paint_main_view(app, window, script, data):
    easel = script.get_object("easel")
    button_start = script.get_object("button_start")
    if button_start is not None and isinstance (button_start, widgets.Button):
        button_start.connect("clicked", easel.clean_up)
        button_start.connect("clicked", lambda *_ : window.stage.destroy())


if __name__ == "__main__":
    pisak.init()
    _paint_app = {
        "app": "paint",
        "type": "clutter",
        "views": [("main", prepare_paint_main_view)]
    }
    app_manager.run(_paint_app)
