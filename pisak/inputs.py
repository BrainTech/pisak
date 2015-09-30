import subprocess
import time
import os
import threading

import pisak
from pisak import logger, exceptions, cursor, scanning, handlers, dirs, \
    tracker

from gi.repository import Gdk, GObject, Clutter
import usb.core


_LOG = logger.get_logger(__name__)

"""
Specification of all the available PISAK input modes.
"""
INPUTS = {
    "mouse": {
        "process": None,
        "middleware": None
    },
    "mouse-switch": {
        "process": None,
        "middleware": {
            "name": "scanning",
            "activator": "InputGroup.launch_scanning_mouse_switch",
            "deactivator": "InputGroup.stop_scanning"
        }
    },
    "keyboard": {
        "process": None,
        "middleware": {
            "name": "scanning",
            "activator": "InputGroup.launch_scanning_keyboard",
            "deactivator": "InputGroup.stop_scanning"
        }
    },
    "eviacam": {
        "process": {
            "command": "eviacam -c",
            "startup": "_wait_on_eviacam_startup"
        },
        "middleware": None
    },
    "tobii": {
        "process": {
            "command": os.path.join(
                dirs.HOME,
                "pisak", "eyetracker", "tobii",
                "pisak-eyetracker-tobii"
            ) + ' --tracking',
            "server": True
        },
        "middleware": {
            "name": "sprite",
            "activator": "InputGroup.launch_sprite",
            "deactivator": "InputGroup.stop_sprite"
        }
    },
    "eyetracker": {
        "process": {
            "command": os.path.join(
                dirs.HOME,
                "pisak", "eyetracker", "camera",
                "pisak-eyetracker-hpe"
            ) + ' --tracking',
            "server": True
        },
        "middleware": {
            "name": "sprite",
            "activator": "InputGroup.launch_sprite",
            "deactivator": "InputGroup.stop_sprite"
        }
    },
    "eyetracker-no-correction": {
        "process": {
            "command": os.path.join(
                dirs.HOME,
                "pisak", "eyetracker", "camera",
                "pisak-eyetracker-hpe"
            ) + ' --tracking --no-translation-correction',
            "server": True
        },
        "middleware": {
            "name": "sprite",
            "activator": "InputGroup.launch_sprite",
            "deactivator": "InputGroup.stop_sprite"
        }
    },
    "eyetracker-mockup": {
        "process": {
            "command": os.path.join(
                dirs.HOME,
                "pisak", "eyetracker", "mockup",
                "pisak-eyetracker-mockup"
            ) + ' --tracking',
            "server": True
        },
        "middleware": {
            "name": "sprite",
            "activator": "InputGroup.launch_sprite",
            "deactivator": "InputGroup.stop_sprite"
        }
    },
    "pisak-switch": {
        "process": None,
        "middleware": {
            "name": "scanning",
            "activator": "InputGroup.launch_scanning_pisak_switch",
            "deactivator": "InputGroup.stop_pisak_switch"
        }
    }
}


class InputsError(exceptions.PisakException):
    pass


class InputGroup(object):
    """
    Group of elements reactive to the same input.

    :param stage: stage that contains the whole group
    """

    def __init__(self, stage):
        super().__init__()
        self.stage = stage
        self.sprite = None
        self.scanning_group = None
        self.content = None
        self.activator = None
        self.deactivator = None
        self.middleware = None
        self.switch_listener = None
        try:
            self.react_on = pisak.config["scanning"].get("react_on") or "release"
        except KeyError:
            msg = "Missing a key from default config - PISAK default config file may be corrupted."
            _LOG.error(msg, pisak.config)
            self.react_on = "release"
        self.action_signal = "button-" + self.react_on + "-event"
        self.scanning_handler = None
        self.input_mode = pisak.config.get("input")
        input_spec = INPUTS.get(self.input_mode)
        if "middleware" in input_spec.keys():
            middleware_spec = input_spec.get("middleware")
            if middleware_spec is None:
                message = "Middleware for input {} not needed.".format(self.input_mode)
                _LOG.debug(message)
            else:
                self.middleware = middleware_spec.get("name")
                self.activator = eval(middleware_spec.get("activator"))
                self.deactivator = eval(middleware_spec.get("deactivator"))
                if not self.middleware or not self.activator or not self.deactivator:
                    message = "No name or no activator or no deactivator declared for input {} " \
                              "middleware. Middleware will not work.".format(self.input_mode)
                    _LOG.critical(message)
                    raise InputsError(message)
        else:
            message = "No specification for input {} middleware.".format(self.input_mode)
            _LOG.critical(message)
            raise InputsError(message)

    def load_content(self, actor):
        """
        Load new, top level object containing all the elements that should
        be reactive to the input events. Launch or schedule launching
        of a activator appropriate for the current input type.

        :param actor: top level UI object
        """
        self.scanning_group = None
        self.content = actor
        self.run_middleware()

    def launch_scanning(self):
        """
        Find the top level scanning group and launch its cycle.
        """
        if self.scanning_group is None:
            self.scanning_group = self._get_toplevel_scanning_group([self.content])
            if self.scanning_group:
                _LOG.debug("Running scanning...")
                self.scanning_group.start_cycle()
        else:
            _LOG.warning("Scanning has been launched already.")

    def launch_scanning_keyboard(self):
        """
        Decorated with 'launch_scanning' function launches scanning and
        connects handler to the proper signal.

        :returns: id of the handler connected to the key release signal
        """
        self.action_signal = "key-" + self.react_on + "-event"
        self.scanning_handler = scanning.Group.key_release
        self.launch_scanning()

    def launch_scanning_mouse_switch(self):
        """
        Decorated with 'launch_scanning' function launches scanning and
        connects handler to the proper signal.

        :returns: id of the handler connected to the button release signal
        """
        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        display.warp_pointer(screen, 5, screen.get_height() - 5)
        self.stage.hide_cursor()
        self.action_signal = "button-" + self.react_on + "-event"
        self.scanning_handler = scanning.Group.button_release
        self.launch_scanning()

    def launch_scanning_pisak_switch(self):
        """
        Decorated with 'launch_scanning' function launches scanning and
        connects handler to the proper signal.

        :returns: id of the handler connected to the key release signal
        """
        if not self.switch_listener:
            self.switch_listener = PisakSwitchListener()
            self.action_signal = "pisak-switch"
            self.scanning_handler = scanning.Group.button_release
        self.launch_scanning()
        self.stage.hide_cursor()

    def get_scanning_desc(self, scanning_group):
        """
        Get description of things necessary for activating the scanning group.

        :param scanning_group: scanning group
        """
        if "key" in self.action_signal:
            signal_source = scanning_group
        elif "pisak-switch" == self.action_signal:
            signal_source = self.switch_listener
        else:
            signal_source = self.stage
        return self.action_signal, self.scanning_handler, signal_source

    def _get_toplevel_scanning_group(self, top_level):
        """
        Get a top-level scanning group from the given object tree.

        :return: top-level scanning group or None.
        """
        next_level = []
        for obj in top_level:
            if isinstance(obj, scanning.Group):
                return obj
            else:
                next_level.extend(obj.get_children())
        if next_level:
            return self._get_toplevel_scanning_group(next_level)

    def launch_sprite(self):
        """
        Initialize sprite and and it to the content scene.
        """
        if self.sprite is None:
            self.sprite = cursor.Sprite()
        if not self.sprite.is_running():
            _LOG.debug("Running sprite...")
            self.sprite.run(self.content)
        else:
            _LOG.warning("Sprite has been launched already.")

    def stop_scanning(self):
        """
        Deactivate scanning.
        """
        if self.scanning_group:
            handlers.kill_group(self.scanning_group)
            self.scanning_group = None
        else:
            _LOG.debug("No scanning running that could be stopped. ")

    def stop_sprite(self):
        """
        Deactivate sprite.
        """
        if self.sprite is not None and self.sprite.is_running():
            self.sprite.stop()
        else:
            _LOG.debug("No sprite running that could be stopped. ")

    def stop_pisak_switch(self):
        """
        Deactivate pisak-switch.
        """
        self.stop_scanning()
        self.switch_listener.listener_destruct()
        self.switch_listener = None

    def run_middleware(self):
        """
        Schedule running the proper middleware.
        """
        if self.content is None:
            message = "Input group has no content. Middleware can not be run."
            _LOG.critical(message)
            raise InputsError(message)
        else:
            if self.activator:
                if self.content.get_property("mapped") or \
                                self.activator == InputGroup.launch_sprite:
                    self.activator(self)
                else:
                    self.content.connect("notify::mapped", lambda *_: self.activator(self))
            else:
                _LOG.debug("No activator specified for the input group "
                           "with input {}.".format(self.input_mode))

    def stop_middleware(self):
        """
        Deactivate the currently running middleware.
        """
        if self.deactivator:
            self.deactivator(self)
        else:
            _LOG.debug("No deactivator specified for the input group "
                       "with input {}.".format(self.input_mode))

class PisakSwitchListener(GObject.GObject):
    """
    Container of methods needed for communicating with pisak-switch device.
    """

    __gsignals__ = {
        "pisak-switch": (
            GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()
        self.endpoint = None
        self.device = None
        self.running = False
        self.signal_size = 8
        self._communication_init()
        self.worker = threading.Thread(target=self._start_loop, daemon=True)
        self.worker.start()

    def _communication_init(self):
        """
        Initialize communication with pisak-switch device. If kernel driver
        has connected with the device, detach it. Writes data about device in
        self.device and self.endpoint.
        """
        usb_manufacturer = "pisak.org"
        usb_product = "pisak-switch"
        while self.device is None:
            for dev in usb.core.find(find_all=True, bDeviceClass=3):
                try:
                    if (dev.manufacturer == usb_manufacturer
                            and dev.product == usb_product):
                        self.device = dev
                        _LOG.debug("Connected with pisak-switch.")
                except usb.core.USBError:
                    msg = "Cannot connect with pisak-switch."
                    _LOG.error(msg, pisak.config)
            time.sleep(1)
        dev_configuration = self.device.get_active_configuration()
        dev_interface = dev_configuration[(0, 0)]
        if self.device.is_kernel_driver_active(dev_interface.bInterfaceNumber):
            self.device.detach_kernel_driver(dev_interface.bInterfaceNumber)
        self.endpoint = usb.util.find_descriptor(dev_interface)
        if self.endpoint is None:
            msg = "Cannot find endpoint."
            _LOG.error(msg, pisak.config)

    def get_signal(self):
        """
        :return: Read data from defined endpoint.
        """
        return self.device.read(self.endpoint.bEndpointAddress,
                                self.signal_size)[0]

    def _start_loop(self):
        """
        Wait for rising slope and send signal when it occurs.
        """
        self.running = True
        previous_state = self.get_signal()
        while self.running:
            current_state = self.get_signal()
            if current_state > previous_state:
                self.emit("pisak-switch")
            previous_state = current_state
            time.sleep(0.01)

    def listener_destruct(self):
        """
        Shuts thread and releases device.
        """
        self.running = False
        self.worker.join()
        usb.util.dispose_resources(self.device)
        _LOG.debug("Pisak-switch disconnected")


def _wait_on_eviacam_startup(process):
    while True:
        out = process.stderr.readline()
        if "Eviacam is ready to go." in str(out):
            break
        time.sleep(0.1)

def run_input_process():
    """
    Check for input type in the default settings and run the
    input as a separate process.

    :returns: process of the input or None and device server or None
    """
    input_mode = pisak.config.get("input")
    _LOG.debug("Input selected: {}.".format(input_mode))
    input_spec = INPUTS.get(input_mode)
    if not input_spec:
        message = "Input {} is not supported. Supported inputs: .".format(
            input_mode, ", ".join(list(INPUTS.keys())))
        _LOG.critical(message)
        raise InputsError(message)
    process_spec = input_spec.get("process")
    if not process_spec:
        message = "Input {} does not require any external process or" \
                  " one has not been specified yet.".format(input_mode)
        _LOG.debug(message)
        return None, None
    command = process_spec.get("command")
    if not command:
        message = "No command specified for the input {}" \
                  "that requires one.".format(input_mode)
        _LOG.critical(message)
        raise InputsError(message)
    _LOG.debug('Running external process "{}"...'.format(command))
    process = subprocess.Popen(command.split(), shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    startup = process_spec.get("startup")
    if startup:
        startup_func = eval(startup)
        startup_func(process)
    _LOG.debug("Process {} was started up and is all ready now.".format(command))
    if not process_spec.get("server"):
        return process, None
    else:
        _LOG.debug("Running tracker server.")
        device_server = tracker.TrackerServer(process)
        device_server.run()
    return process, device_server
