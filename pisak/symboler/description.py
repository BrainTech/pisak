"""
Descriptor for symboler application.
"""

from pisak import handlers # @UnusedImport

import pisak.symboler.widgets  # @UnusedImport
import pisak.symboler.handlers  # @UnusedImport


def prepare_symboler_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")


symboler_app = {
    "app": "symboler",
    "type": "clutter",
    "views": [("main", prepare_symboler_view)]
}
