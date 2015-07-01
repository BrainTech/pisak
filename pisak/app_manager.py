"""
Module contains tools responsible for management of Pisak applications,
that is, launching them as stand-alone proccesses
handling their closure and switching between them.
It also contains the waiting panel that is launched in order to indicate
that some application is being loaded.
"""
import subprocess
import threading
import importlib
import sys
import traceback

from gi.repository import GObject, Clutter, Mx

import pisak
from pisak import application, logger
from pisak.libs import configurator, properties, widgets, arg_parser

_LOG = logger.get_logger(__name__)

MESSAGES = {
    "application_loading": "Wczytywanie aplikacji..."
}


### PISAK applications entry point.  ###
def run(descriptor):
    """
    Run an application.

    :param descriptor: dictionary containing general application description.
    It should specify what type of application should be launched and provide
     all the basic data required for a proper application functioning.
     It should contain following items: 'type' - type of an application
     to be launched ('clutter' or 'gtk'); 'app' - name of the application;
     'views' - list of all the application views, each view is a tuple with
     the view name and a function responsible for the view preparation.
    """
    pisak.app = None

    app_type = descriptor['type']
    if app_type == 'clutter':
        AppType = application.ClutterApp
    elif app_type == 'gtk':
        AppType = application.GtkApp
    else:
        raise RuntimeError('Unknown application type!')

    pisak.app = AppType(arg_parser.get_args(), descriptor)

    pisak.app.window.load_initial_view()
    pisak.app.main()

    pisak.app = None


### Section with management tools of PISAK applications' 'executables'. ###

class LoadingStage(Clutter.Stage):
    """
    Stage for the time a new app is being loaded.
    """

    def __init__(self):
        super().__init__()
        self.set_layout_manager(Clutter.BinLayout())
        self._init_background()
        self._init_text()

    def _init_background(self):
        background = widgets.BackgroundPattern()
        background.ratio_width = 1
        background.ratio_height = 1
        self.add_child(background)

    def _init_text(self):
        text = Mx.Label()
        text.set_style_class("LoadingPanel")
        text.set_text(MESSAGES["application_loading"])
        text.set_x_align(Clutter.ActorAlign.CENTER)
        text.set_y_align(Clutter.ActorAlign.CENTER)
        self.add_child(text)


class AppManager(Clutter.Actor,
                 configurator.Configurable,
                 properties.PropertyAdapter,
                 widgets.ButtonSource):
    """
    Class for launching and managing various Pisak applications' 'executables'.
    Applications to be available within the given Pisak session can be
    specified in a global configuration file.
    """
    __gtype_name__ = "PisakAppManager"

    def __init__(self):
        super().__init__()
        self.current_app = None
        self.apps = []
        self.apply_props()
        self.loading_stage = LoadingStage()

    def launch_app(self, app_descriptor):
        """
        Launch an app with the given descriptor.

        :param app_descriptor: :see: :func: run
        """
        run(app_descriptor)

    def get_buttons_descriptor(self):
        """
        Implementation of the widgets.ButtonSource method for getting
        buttons responsible for launching proper applications.

        :return: list of available buttons descriptions
        """
        buttons_list = []
        for app, values in self.apps.items():
            desc = {
                "exec_path": self._get_exec_path(values["module"]),
                "icon_size": values["icon_size"],
                "icon_name": values["icon_name"],
                "label": values["label"],
                "style_class": "PisakMainPanelButton"
            }
            buttons_list.append(desc)
        return buttons_list

    def minimize_panel(self):
        """
        Deactivate the main panel and all its content.
        """
        pisak.app.window.input_group.stop_middleware()
        self.loading_stage.show()
        if not arg_parser.get_args().debug:
            self.loading_stage.set_fullscreen(True)

    def maximize_panel(self, event):
        """
        Reactivate the main panel and all its content.
        """
        self.loading_stage.hide()
        pisak.app.window.input_group.run_middleware()

    def run_app(self, button, app_exec):
        """
        Run an app with the given name as a new subprocess.
        Hide the current app stage.

        :param app_exec: name of an app
        """
        if self.current_app is None:
            self.minimize_panel()
            worker = threading.Thread(
                target=self._do_run_app,
                args=(app_exec, ),
                daemon=True
            )
            worker.start()

    def _do_run_app(self, app_exec):
        cmd = ["python3", app_exec] + sys.argv[1:] + ["--child"]
        self.current_app = subprocess.Popen(cmd)
        self.current_app.wait()
        Clutter.threads_add_idle(0, self.maximize_panel, None)
        self.current_app = None

    def _get_exec_path(self, module_name):
        return importlib.import_module(".".join(["pisak.apps",
                                                 module_name])).EXEC_PATH
