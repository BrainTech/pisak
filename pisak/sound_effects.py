"""
Sound effects player.
"""
import subprocess
import threading

import gi
gi.require_version('Gst', '1.0')

from gi.repository import GObject, Gst

import pisak
from pisak import arg_parser
from pisak import logger

_LOG = logger.get_logger(__name__)


GObject.threads_init()
Gst.init(arg_parser.get_args().args)


class SoundEffectsPlayer(object):
    def __init__(self, sounds_dict):
        super().__init__()
        self.sounds = sounds_dict
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        self._playbin.set_property("volume",
                                   pisak.config.as_int('sound_effects_volume') / 100)
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self.on_message)

    def play(self, sound_name):
        self._playbin.set_property("volume",
                                   pisak.config.as_int('sound_effects_volume') / 100)
        self._playbin.set_state(Gst.State.READY)
        if sound_name in self.sounds:
            self._playbin.set_property('uri', 'file://' + self.sounds[sound_name])
        else:
            self._playbin.set_property('uri', 'file://' + sound_name)
        self._bus.add_signal_watch()
        self._playbin.set_state(Gst.State.READY)
        self._playbin.set_state(Gst.State.PLAYING)

    def on_message(self, _bus, message):
        if message.type == Gst.MessageType.EOS:
            self.free_resource()
        elif message.type == Gst.MessageType.ERROR:
            _LOG.warning("An error occured while playing file: " +\
                         str(self._playbin.get_property('uri')))
            self.free_resource()
            
    def free_resource(self):
        self._bus.remove_signal_watch()
        self._playbin.set_state(Gst.State.NULL)
        msg = 'Resources freed from playbin with file: ' +\
              str(self._playbin.get_property('uri'))
        _LOG.debug(msg)

def sec_converter(seconds):
    seconds = int(seconds)

    minutes = seconds // 60
    seconds = seconds - (minutes*60)

    return "{0:02d}:{1:02d}".format(minutes, seconds)

class Synthezator(object):
    def __init__(self, text):
        self.text = text
        self.process = None

    def read(self, timeout=None):
        if timeout is None or timeout <= 0:
            process = subprocess.Popen(["milena_say", self.text])
            process.wait()
        else:
            scan_time = sec_converter(timeout)
            call = 'milena_say "-S trim 0 {}" {}'.format(scan_time, self.text)
            self.process = subprocess.Popen([call], shell=True)
