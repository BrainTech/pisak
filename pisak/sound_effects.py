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

class Sound(object):
    def __init__(self, path, player):
        super().__init__()
        self._path = path
        self._playbin = player._playbin
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self.on_message)

    def play(self):
        self._playbin.set_property('uri', 'file://' + str(self._path))
        self._bus.add_signal_watch()
        self._playbin.set_state(Gst.State.READY)
        self._playbin.set_state(Gst.State.PLAYING)

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
    
class SoundEffectsPlayer(object):
    def __init__(self, sounds_list):
        super().__init__()
        self.sounds = {}
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        CHANNELS_PER_FILE = 1
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
            # volumes[sound_name] = volume
            vec = []
            for i in range(CHANNELS_PER_FILE):
                vec.append(Sound(config['file_name'],self))
            self.sounds[sound_name] = tuple(vec)
            # print('xxx: ' + str(self.sounds))

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name][0].play()
        else:
            _LOG.warning('Sound not found.')

    def set_volume(self, volume):
        pass

    def shutdown(self):
        pass
