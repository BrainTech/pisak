"""
Sound effects player.
"""
import gi
gi.require_version('Gst', '1.0')

from gi.repository import GObject, Gst

from pisak import logger


_LOG = logger.get_logger(__name__)


GObject.threads_init()
Gst.init()


class SoundEffectsPlayer(object):
    def __init__(self, sounds_dict):
        super().__init__()
        self.sounds = sounds_dict
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self.on_message)

    def play(self, sound_name):
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
