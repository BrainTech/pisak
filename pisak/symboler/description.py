"""
Descriptor for symboler application.
"""

from pisak import res, handlers
from pisak.symboler import symbols_manager

import pisak.symboler.widgets  # @UnusedImport
import pisak.symboler.handlers  # @UnusedImport

def prepare_symboler_view(app, window, script, data):
    symbols_manager.create_model()
    handlers.button_to_view(window, script, "button_exit")
    
symboler_app = {
    "app": "symboler",
    "type": "clutter",
    "views": [("main", prepare_symboler_view)]
}
