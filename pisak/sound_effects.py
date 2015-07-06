"""
Sound effects player.
"""
from gi.repository import ClutterGst


class SoundEffectsPlayerNative:
    def __init__(self, sounds_list):
        ClutterGst.init()

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
                s = ClutterGst.VideoTexture()
                s.set_filename(config['file_name'])
                s.set_buffering_mode(ClutterGst.BufferingMode.DOWNLOAD)  # DOWNLOAD
                vec.append(s)
            self.sounds[sound_name] = tuple(vec)
            # print('xxx: ' + str(self.sounds))

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name][0].set_playing(True)
        else:
            print('sound not found')

    def set_volume(self, volume):
        pass

    def shutdown(self):
        pass


SoundEffectsPlayer = SoundEffectsPlayerNative
