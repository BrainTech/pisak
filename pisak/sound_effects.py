#!/usr/bin/env python3

import multiprocessing


def _sound_effects_process(queue, sounds_list):
    """
    Main function of sound effects process.

    Sound effects process asynchronously loads specified sounds
    and starts an event loop waiting for commands from master process.

    :param queue: Queue used for interprocess communication.
    :type queue: multiprocessing.Queue.
    :param sounds_list: Dictionary with sounds specification.
    :type sounds_list: dict.
    """
    import sys
    from PyQt5.QtCore import QCoreApplication, QTimer, QUrl
    from PyQt5.QtMultimedia import QSoundEffect

    def log(msg):
        import os
        from datetime import datetime

        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ': '
        print(timestamp + msg)
        try:
            with open(os.path.join(os.path.expanduser('~'),
                                   '.pisak', 'logs', 'sound_effects.log'), 'a') as f:
                f.write(timestamp + msg + '\n')
        except Exception as ex:
            print(ex)

    log('Sounds list:\n' + str(sounds_list))

    CHANNELS_PER_FILE = 2
    DEFAULT_CONFIG = {
        'file_name': '',
        'volume': 1.0,
        'loop_count': 1
    }

    sounds = {}
    volumes = {}
    timer = QTimer()
    # from PyQt5.QtWidgets import QApplication
    app = QCoreApplication(sys.argv)

    # from PyQt5.QtWidgets import QWidget
    # widget = QWidget()
    # widget.show()

    def init_sounds():
        for sound_name, value in sounds_list.items():
            config = DEFAULT_CONFIG.copy()
            if isinstance(value, dict):
                config.update(value)
            else:
                config['file_name'] = value
            volume = float(config['volume'])
            volumes[sound_name] = volume
            vec = []
            for i in range(CHANNELS_PER_FILE):
                s = QSoundEffect(app)
                s.statusChanged.connect(
                    lambda i=i, s=s:
                    log('stateChanged: {}: {}: {}'.format(s.source().toLocalFile(), i, s.status()))
                )
                s.setLoopCount(int(config['loop_count']))
                s.setVolume(volume)
                s.setSource(QUrl.fromLocalFile(config['file_name']))
                vec.append(s)
            sounds[sound_name] = tuple(vec)

        # log('xxx: ' + str(sounds))

        # start polling for messages
        def proc():
            # while not queue.empty():
            #    queue.get(False)
            timer.start(10)

        QTimer.singleShot(500, proc)

    def set_volume(new_global_volume):
        for sound_volume, s_v in zip(volumes.values(), sounds.values()):
            volume = max(min(sound_volume * new_global_volume, 1.0), 0.0)
            for s in s_v:
                s.setVolume(volume)

    def check_queue():
        if queue.empty():
            return
        try:
            sound_name = queue.get(False)
            if sound_name in sounds:
                log('requested sound: {}'.format(sound_name))
                # Try to find first idle sound and play it. If all sounds are
                # currently playing restart one of them.
                s_v = sounds[sound_name]
                for s in s_v:
                    if not s.isLoaded():
                        log('sound {} is not loaded (status: {})'.format(sound_name, s.status()))
                    if not s.isPlaying():
                        s.play()
                        break
                else:
                    if not s_v[0].isLoaded():
                        log('sound {} is not loaded (status: {})'.format(sound_name, s.status()))
                    s_v[0].play()
            elif sound_name == '__exit__':
                app.quit()
            elif sound_name.startswith('__volume__:'):
                try:
                    set_volume(float(sound_name.replace('__volume__:', '')))
                except Exception as ex:
                    log('Error setting volume: {}'.format(ex))
                    pass
            else:
                log('Unknown sound name: {}'.format(str(sound_name)))
                pass
        except Exception as ex:
            log('Sound effects process: queue.get failed: {}'.format(ex))
            pass

    timer.timeout.connect(check_queue)
    QTimer.singleShot(100, init_sounds)
    ret = app.exec_()
    log('Sound effects process finished with code: {}'.format(ret))


class SoundEffectsPlayerMultiprocessing:
    """
    Class for controlling sound effects player process.

    Remember to call shutdown when effects player is no longer needed, otherwise
    application may hang instead of closing.

    Example sounds_list::

        sounds_list = {
            'xx': {
                'file_name': 'xx.wav',
                'volume': 0.5,
                'loop_count': 1
            },
            'yy': 'yy.wav',
            'zz': '/full/path/to/file/zz.wav'
        }

    """

    def __init__(self, sounds_list):
        """
        Create sound effects player process and load specified sounds.

        :param sounds_list: Dictionary with sounds specification.
        :type sounds_list: dict
        """
        self._ctx = multiprocessing.get_context('spawn')
        self._queue = self._ctx.Queue()
        self._sounds_process = self._ctx.Process(
            target=_sound_effects_process,
            args=(self._queue, sounds_list))
        self._sounds_process.start()

    def play(self, sound_name):
        """
        Play specified sound. This function can be called multiple times with the same
        sound_name, but a single sound will simultaneously play no more than
        CHANNELS_PER_FILE times. Requested sounds are queued and should be played back with
        a typical delay of 1-5 ms.

        :param sound_name: Sound name.
        :type sound_name: str
        """
        self._queue.put(sound_name)

    def set_volume(self, volume):
        """
        Set maximum volume for sound effects. Relative volumes of individual sounds
        can be set independently in __init__ method.

        :param volume: Real number from 0.0 to 1.0.
        :type volume: float
        """
        self._queue.put('__volume__:{:.4f}'.format(volume))

    def shutdown(self):
        """
        Close sound effects player process. Subprocess is asked to shutdown
        gracefully. If it's still running after 1 s, child process is
        forcibly terminated.
        """
        if self._sounds_process.is_alive():
            self._queue.put('__exit__')
            self._sounds_process.join(1.0)
            if self._sounds_process.is_alive():
                self._sounds_process.terminate()


class SoundEffectsPlayerNative:
    def __init__(self, sounds_list):
        from gi.repository import GObject, ClutterGst, Clutter

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


SoundEffectsPlayer = SoundEffectsPlayerMultiprocessing

if __name__ == '__main__':
    import random

    class QueueMock:
        def __init__(self):
            self.counter = 0
            self.is_empty = False

        def empty(self):
            self.counter += 1
            if self.counter % 10 == 0:
                self.counter = 0
                return False
            else:
                return True

        def get(self, xx):
            return random.choice(['scanning', 'selection'])

    queue = QueueMock()
    sounds_list = {
        'selection': '/home/alex/pisak/pisak/res/sounds/beep.wav',
        'scanning': '/home/alex/pisak/pisak/res/sounds/button-28.wav'
    }
    _sound_effects_process_pyglet(queue, sounds_list)
