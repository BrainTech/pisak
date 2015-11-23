"""
Descriptor for Budzik application.
"""

from pisak import res, handlers
from pisak import widgets  # @UnusedImport
import pisak.handlers  # @UnusedImport


def prepare_main_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")

budzik_app = {
    "app": "budzik",
    "type": "clutter",
    "views": [("main", prepare_main_view)]
}
