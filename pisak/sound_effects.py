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
    def __init__(self, sounds_list):
        super().__init__()
        self.sounds = {}
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self.on_message)
        DEFAULT_CONFIG = {
            'file_name': '',
            'volume': 1.0,
            'loop_count': 1
        }

        for sound_name, value in sounds_list.items():
            config = DEFAULT_CONFIG.copy()
            if isinstance(value, dict):
                config.update(value)
            else:
                config['file_name'] = value
            volume = float(config['volume'])
            self.sounds[sound_name] = config['file_name']
            # print('xxx: ' + str(self.sounds))

    def play(self, sound_name, sound_dict = None):
        if sound_dict == None:
            sound_dict = self.sounds
        if sound_name in sound_dict:
            self._playbin.set_state(Gst.State.READY)
            self._playbin.set_property('uri', 'file://' + sound_dict[sound_name])
            self._bus.add_signal_watch()
            self._playbin.set_state(Gst.State.READY)
            self._playbin.set_state(Gst.State.PLAYING)
        else:
            _LOG.warning('Sound not found.')

    def on_message(self, bus, message):
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

    def set_volume(self, volume):
        pass

    def shutdown(self):
        pass
