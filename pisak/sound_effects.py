"""
Sound effects player.
"""
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
        self._volume = pisak.config.as_int('sound_effects_volume') / 100
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        self._playbin.set_property("volume", self.volume)
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self.on_message)

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        vol = float(value)
        if 0 <= vol <= 1:
            self._volume = vol
            self._playbin.set_property("volume", vol)
        else:
            msg = "Provided value must be between 0 and 1. Received {}."
            _LOG.error(msg.format(vol))
        
    def play(self, sound_name):
        self.volume = self.volume
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
