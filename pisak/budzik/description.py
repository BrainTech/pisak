"""
Descriptor for Budzik application.
"""
from pisak import widgets, res, handlers  # @UnusedImport
import pisak.speller.widgets # @UnusedImport
import pisak.speller.handlers # @UnusedImport
import pisak.budzik.handlers # @UnusedImport


def prepare_main_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")


budzik_app = {
    "app": "budzik",
    "type": "clutter",
    "views": [("main", prepare_main_view)]
}
