'''
Module which manages the application main window and all the application views.
'''
import os

from gi.repository import Clutter, Mx

from pisak import exceptions
from pisak import signals, configurator, dirs, inputs, widgets

import pisak.layout  # @UnusedImport
import pisak.handlers  # @UnusedImport


def prepare_popup_view(app, window, script, data):
    """
    Prepare pop-up view, displayed on some special situations.

    :param app: current application instance.
    :param window: current application main window instance.
    :param script: current view ClutterScript.
    :param data: some extra, view-specific data.
    """
    window.ui.message.set_text(data["message"])


BUILTIN_VIEWS = [
    ("popup", prepare_popup_view)
]


class WindowError(exceptions.PisakException):
    """
    Error thrown when application window meets an unexpected condition.
    """
    pass


class _UI:
    """
    User interface definition plain container.

    :param script: UI script.
    """
    def __init__(self, script):
        for obj in script.list_objects():
            if hasattr(obj, "get_id"):
                setattr(self, obj.get_id(), obj)


class Window(configurator.Configurable):
    """
    Any PISAK application main window class. It manages different views,
    switches between them, manages a view layout.
    """

    def __init__(self, application, stage, descriptor):
        super().__init__()
        # instance of an application that the window belongs to:
        self.application = application

        # backend-specific window stage, base widget instance:
        self.stage = stage

        # instance of :see: :class: `_UI`, container for UI elements:
        self.ui = None

        # type of the window backend:
        self.type = None

        # name of the application that the window belongs to
        self.app_name = None

        # handler of the main input device:
        self.input_group = inputs.InputGroup(self.stage)

        # pending scanning group:
        self.pending_group = None

        self._init_layout()
        self._read_descriptor(descriptor)

    def load_initial_view(self, on_init=None):
        """
        Load initial view of the application.

        :param on_init: function to be called before loading the initial view.
        """
        if callable(on_init):
            if not on_init(self):
                return

        self.load_view(self.initial_view)

    def _init_layout(self):
        '''Each class should implement it's own specific layout'''
        self.stage.set_layout_manager(Clutter.BinLayout())

    def _read_descriptor(self, descriptor):
        """
        Read the given descriptor. Valid descriptor must be in a form
        of a dictionary and should contain following keys: 'views' and
        'app', that are obligatory. 'app' is a string name of an application;
        'views' is a list of tuples, each consisting of the name of a single
        view and callable that is responsible for preparing that view.

        :param descriptor: dictionary that unambiguously describes
        an application that should be prepared and launched.
        """
        self.type = descriptor["type"]
        self.app_name = descriptor.get("app")
        self._read_config()
        self._read_views(descriptor.get("views"))
        self.initial_view = os.path.join(self.app_name, "main")

    def _read_config(self):
        """
        Extract configuration parameters for the current application.
        Currently, these are optional and can influence only:
        type of views content that will replace their default content.
        """
        self.apply_props()
        self._configuration = self.config["PisakAppManager"]["apps"].get(self.app_name)

    def _read_views(self, view_list):
        """
        Translate the view list received in the descriptor into the one
        understood by the views loader.
        Add any extra, built-in views with the `_add_builtin_views` method.

        :param view_list: list of tuples of avalaible views, each consists
        of view name and view callable preparator.
        """
        skin = self.config['skin']
        speller_layout = self.config['speller']['layout']
        layout = 'default'
        if self.app_name in ['speller', 'blog', 'email']:
            layout = speller_layout
        if self._configuration:
            special_layout = self._configuration.get("layout")
            if special_layout:
                layout = special_layout
        layout = '_'.join([layout, skin])
        self.views = {}
        for view_name, preparator in view_list:
            self.views[os.path.join(self.app_name, view_name)] = (
                dirs.get_json_path(view_name, layout, self.app_name), preparator
            )
        self._add_builtin_views(self.views, layout)

    def _add_builtin_views(self, views_dict, layout):
        for view_name, preparator in BUILTIN_VIEWS:
            views_dict[view_name] = (
                dirs.get_json_path(view_name, layout), preparator)

    def load_view(self, name, data=None):
        """
        Loads a given view. Replaces previous view, if any. Triggers
        the input management system..

        :param name: name of a view.
        :param data: optional, some extra data.
        """
        if name not in self.views.keys():
            message = "Descriptor has no view with name: {}".format(name)
            raise WindowError(message)
        view_path, prepare = self.views.get(name)
        self.script = Clutter.Script()
        self.script.load_from_file(view_path)
        self.script.connect_signals_full(
            signals.connect_registered, self.application)
        self.ui = _UI(self.script)
        if callable(prepare):
            prepare(self.application, self, self.script, data)
        children = self.stage.get_children()
        main_actor = self.script.get_object("main")
        if children:
            self.input_group.stop_middleware()
            old_child = children[0]
            self.stage.replace_child(old_child, main_actor)
        else:
            self.stage.add_child(main_actor)
        self.input_group.load_content(main_actor)

    def load_popup(self, message, unwind=None, unwind_data=None,
                   container=None, timeout=5000):
        """
        Load a pop-up view with some message displayed and then, after a
        given amount of time automatically load some another view or
        perform some operation.

        :param message: message to be displayed on the screen.
        :param unwind: name of a view that should be loaded after
        the `timeout` expires or callable that should be called then or None.
        :param unwind_data: data to be passed to an unwind handler or None.
        :param container: container that popup should be added to or None,
        if None then it will be displayed as a standard standalone view.
        :param timeout: time after which the `unwind`
        will be executed automatically, in miliseconds, default is 1 second, if -1 then
        the `unwind` to will not be executed at all.

        :return: None.
        """
        if timeout >= 0 and unwind is not None:
            if callable(unwind):
                handler = (lambda *_: unwind(unwind_data)) if \
                          unwind_data is not None else lambda *_: unwind()
            else:
                if unwind.split('/')[0] == 'main_panel' and self.app_name != 'main_panel':
                    handler = lambda *_: self.application.main_quit()
                else:
                    handler = lambda *_: self.load_view(unwind, unwind_data)

            Clutter.threads_add_timeout(0, timeout, handler)

        if container:
            self._display_popup_widget(container, message)
        else:
            self.load_view("popup", {"message": message})

    def _display_popup_widget(self, container, message):
        popup = widgets.Label()
        popup.set_text(message)
        popup.set_style_class("PisakPopUp")
        container.add_child(popup)
