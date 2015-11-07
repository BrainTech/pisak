"""
Descriptor for Speller application.
"""

from pisak import res, handlers
from pisak.speller import widgets  # @UnusedImport
import pisak.speller.handlers  # @UnusedImport


def prepare_main_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")

    from pisak.obci_scanner import Scanner
    scanner = Scanner(window.ui.keyboard_panel)
    scanner.start()


speller_app = {
    "app": "speller",
    "type": "clutter",
    "views": [("main", prepare_main_view)]
}
