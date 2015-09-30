"""
Descriptor for symboler application.
"""

from pisak import handlers # @UnusedImport

import pisak.symboler.widgets  # @UnusedImport
import pisak.symboler.handlers  # @UnusedImport

def prepare_symboler_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    
symboler_app = {
    "app": "symboler",
    "type": "clutter",
    "views": [("main", prepare_symboler_view)]
}
