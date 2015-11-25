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
    """
    Player of some simple sound effects. Audio files are loaded just
    once when registered and then they are stored and available in a sounds pool,
    throughout the class' entire lifetime.

    :param sounds_dict: dictionary of sounds.
    """

    def __init__(self, sounds_dict):
        super().__init__()
        self.sounds = sounds_dict
        self._volume = pisak.config.as_int('sound_effects_volume') / 100
        self._playbin = Gst.ElementFactory.make('playbin', 'button_sound')
        self._playbin.set_property("volume", self.volume)
        self._bus = self._playbin.get_bus()
        self._bus.connect('message', self._on_message)

    @property
    def volume(self):
        """
        Common volume level, normalized value between 0 and 1.
        """
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
        """
        Play a sound. Sounds are played in a thread-safe, non-blocking manner.

        :param sound_name: name of a previously registered sound.
        """
        self.volume = self.volume
        self._playbin.set_state(Gst.State.READY)
        if sound_name in self.sounds:
            self._playbin.set_property('uri', 'file://' + self.sounds[sound_name])
        else:
            self._playbin.set_property('uri', 'file://' + sound_name)
        self._bus.add_signal_watch()
        self._playbin.set_state(Gst.State.READY)
        self._playbin.set_state(Gst.State.PLAYING)
            
    def _free_resource(self):
        self._bus.remove_signal_watch()
        self._playbin.set_state(Gst.State.NULL)
        msg = 'Resources freed from playbin with file: ' +\
              str(self._playbin.get_property('uri'))
        _LOG.debug(msg)

    def _on_message(self, _bus, message):
        if message.type == Gst.MessageType.EOS:
            self._free_resource()
        elif message.type == Gst.MessageType.ERROR:
            _LOG.warning("An error occured while playing file: " +\
                         str(self._playbin.get_property('uri')))
            self._free_resource()


class Synthesizer(object):
    """
    Speech synthesizer. Uses Milena text-to-speech program.

    :param text: text to be read, string.
    """
    def __init__(self, text):
        self.text = text
        self.process = None

    @staticmethod
    def _sec_converter(seconds):
        """
        Converts seconds to minutes and seconds, formats an output properly,
        for the Milena program exclusively.

        :param seconds: number of seconds, can be string, int or float.

        :return: properly formatted number of minutes and seconds, string.
        """
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds - (minutes*60)
        return "{0:02d}:{1:02d}".format(minutes, seconds)

    def read(self, timeout=None):
        """
        Read the text out loud. Milena is spawned as a subprocess
        in a non-blocking mode.

        :param timeout: optional, max number of seconds
        that the reading should be limited to.
        """
        if timeout is None or timeout <= 0:
            self.process = subprocess.Popen(["milena_say", self.text])
        else:
            timeout = self._sec_converter(timeout)
            if pisak.arg_parser.get_args().debug:
                call = 'milena_say "-S trim 0 {}" {}'
            else:
                call = 'milena_say "-S trim 0 {}" {} 2>/dev/null'
            self.process = subprocess.Popen([call.format(timeout,
                                                         self.text)],
                                            shell=True)

    def read_and_call(self, func_to_call, timeout=None):
        """
        Read the text out loud and then, when finished,
        call some function. Everything is executed
        from a separate thread.

        :param func_to_call: function to be called.
        """
        def worker():
            self.read(timeout)
            self.process.wait()
            func_to_call()
            
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
