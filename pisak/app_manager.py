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

import gi

gi.require_version('Clutter', '1.0')
gi.require_version('Mx', '1.0')

from gi.repository import GObject, Clutter, Mx

import pisak
from pisak import application, logger, configurator, properties,\
    widgets, arg_parser, inputs, dirs

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
    input_process = None
    device_server = None
    if '--child' not in sys.argv:
        input_process, device_server = inputs.run_input_process()

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

    if input_process:
        input_process.terminate()
    if device_server:
        device_server.stop()


### Section with management tools of PISAK applications' 'executables'. ###

class LoadingScreen(Clutter.Stage):
    """
    Screen displayed when a new app is being loaded.
    """

    def __init__(self):
        super().__init__()
        self._init_content()

    def _init_content(self):
        self.set_layout_manager(Clutter.BinLayout())
        json = dirs.get_json_path('loading_screen', '_'.join(
            ['default', pisak.config['skin']]))
        script = Clutter.Script()
        script.load_from_file(json)
        main = script.get_object('main')
        self.add_actor(main)


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
        self.loading_screen = LoadingScreen()

    @staticmethod
    def launch_app(app_descriptor):
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
        available = pisak.config['available_apps']
        for app, values in self.apps.items():
            if app in available and available.as_bool(app) and app != 'main_panel':
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
        self.loading_screen.show()
        if not arg_parser.get_args().debug:
            self.loading_screen.set_fullscreen(True)

    def maximize_panel(self, event):
        """
        Reactivate the main panel and all its content.
        """
        self.loading_screen.hide()
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
        cmd = [app_exec] + sys.argv[1:] + ["--child"]
        self.current_app = subprocess.Popen(cmd)
        self.current_app.wait()
        Clutter.threads_add_idle(0, self.maximize_panel, None)
        self.current_app = None

    def _get_exec_path(self, module_name):
        return 'pisak-' + str(module_name)
