"""
Descriptor for Speller application.
"""

from pisak import res, handlers
from pisak.speller import widgets  # @UnusedImport
import pisak.speller.handlers  # @UnusedImport


def prepare_main_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    
    from pisak.obci_scanner import Scanner
    scanner = Scanner(window.ui.keyboard_panel)
    scanner.run_scenario([(('row', 'random-replacement-greedy'), 2100),
                          (('column', 'order'), 1100),
                          (('element', 'random-replacement'), 1500)])


speller_app = {
    "app": "speller",
    "type": "clutter",
    "views": [("main", prepare_main_view)]
}
