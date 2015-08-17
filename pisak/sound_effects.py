"""
Sound effects player.
"""
from gi.repository import Gst
from pisak import logger

_LOG = logger.get_logger(__name__)

class SoundEffectsPlayer:
    def __init__(self, sounds_list):
        Gst.init()

        self.sounds = {}

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
                playbin = Gst.ElementFactory.make('playbin')
                playbin.set_property('uri', 'file://' + config['file_name'])
                vec.append(playbin)
            self.sounds[sound_name] = tuple(vec)
            # print('xxx: ' + str(self.sounds))

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name][0].set_state(Gst.State.READY)
            self.sounds[sound_name][0].set_state(Gst.State.PLAYING)
        else:
            _LOG.warning('Sound not found.')

    def set_volume(self, volume):
        pass

    def shutdown(self):
        pass
