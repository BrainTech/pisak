"""
Main module of the symboler application. Launching and managing all the
application's views takes place here.
"""
import sys

import pisak
from pisak import app_manager, res
from pisak.libs import handlers
from pisak.libs.symboler import symbols_manager

import pisak.libs.symboler.widgets  # @UnusedImport
import pisak.libs.symboler.handlers  # @UnusedImport


def prepare_symboler_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")


if __name__ == "__main__":
    pisak.init()
    _symboler_app = {
        "app": "symboler",
        "type": "clutter",
        "views": [("main", prepare_symboler_view)]
    }
    symbols_manager.create_model()
    app_manager.run(_symboler_app)
