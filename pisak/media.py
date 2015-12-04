"""
Module offering tools for managing and playing different kinds of media data.
"""

from multiprocessing import Process, Manager, Event

from gi.repository import GObject, ClutterGst, Clutter

import pisak
from pisak import res
from pisak import properties, configurator


class MediaPlaybackIface:
    """
    Interface of players of different kinds of media data.
    """

    def play(self):
        """
        Start playing the media stream.
        """
        raise NotImplementedError

    def stop(self):
        """
        Stop playing the media stream.
        """
        raise NotImplementedError

    def pause(self):
        """
        Pause playing the media stream.
        """
        raise NotImplementedError

    def is_playing(self):
        """
        Return the status of the media stream.
        """
        raise NotImplementedError

    def get_duration(self):
        """
        Get duration of the media stream.
        """
        raise NotImplementedError

    def rewind_to(self, position):
        """
        Rewind the media stream to the given position.

        :param position: new position
        """
        raise NotImplementedError

    def rewind_forward(self):
        """
        Rewind the media stream forward.
        """
        raise NotImplementedError

    def rewind_backward(self):
        """
        Rewind the media stream backward.
        """
        raise NotImplementedError

    def increase_volume(self):
        """
        Increase volume of the media stream.
        """
        raise NotImplementedError

    def decrease_volume(self):
        """
        Decrease volume of the media stream.
        """
        raise NotImplementedError

    def set_volume(self, value):
        """
        Set volume of the media stream to the given value.

        :param value: new volume value
        """
        raise NotImplementedError

    def get_elapsed_time(self):
        """
        Get elapsed time of the media stream.
        """
        raise NotImplementedError


class MediaPlayback(Clutter.Actor, MediaPlaybackIface,
                    properties.PropertyAdapter, configurator.Configurable):
    """
    Tool for controlling playback of different kinds of media data,
    being a wrapper of an inernal ClutterMedia.
    """

    __gsignals__ = {
        "progressed": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_FLOAT, GObject.TYPE_FLOAT,)),
        "started-playing": (
            GObject.SIGNAL_RUN_FIRST, None, ()),
        "eos": (
            GObject.SIGNAL_RUN_FIRST, None, ()),
        "limit-declared": (
            GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_FLOAT,))
    }
    __gproperties__ = {
        "rewind_step": (
            GObject.TYPE_FLOAT, None, None,
            0, GObject.G_MAXUINT, 2, GObject.PARAM_READWRITE),
        "skip_step": (
            GObject.TYPE_FLOAT, None, None,
            0, GObject.G_MAXUINT, 30, GObject.PARAM_READWRITE),
        "volume_step": (
            GObject.TYPE_FLOAT, None, None,
            0, 1, 0.05, GObject.PARAM_READWRITE),
        "engine": (
            Clutter.Actor.__gtype__,
            "", "", GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self._engine = None
        self.rewind_direction = None
        self.rewind_step = 3
        self.skip_step = 30
        self.volume_step = 0.1
        self.volume = pisak.config.as_int('sound_effects_volume') / 100
        self.rewind_pace = 200  # pace of rewinding in miliseconds
        self.rewind_timer_handler = None
        self.rewind_timer = Clutter.Timeline.new(self.rewind_pace)
        self.rewind_timer.set_repeat_count(-1)
        self.filename = ""
        # needed as fail safe for sudden progress jumps
        self.previous_progress = 0
        self.apply_props()

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        """
        Engine to be used for streaming media content. At the moment it
        should be ClutterMedia. When set, default audio volume level is applied
        and handler is connected to signal emitted on media progress changes.

        :param value: instance of an engine.
        """
        self._engine = value
        if value is not None:
            value.connect("notify::progress", self._on_progressed)
            value.set_audio_volume(self.volume)

    @property
    def rewind_step(self):
        """
        Step of rewinding in seconds.
        """
        return self._rewind_step

    @rewind_step.setter
    def rewind_step(self, value):
        self._rewind_step = value

    @property
    def skip_step(self):
        """
        Step of skipping in seconds.
        """
        return self._skip_step

    @skip_step.setter
    def skip_step(self, value):
        self._skip_step = value

    @property
    def volume_step(self):
        """
        Step of volume changes.
        """
        return self._volume_step

    @volume_step.setter
    def volume_step(self, value):
        self._volume_step = value

    @property
    def filename(self):
        """
        Path to the file with media stream. Setting this property
        cause loading of a media stream to the player.
        """
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
        if value is not None and self.engine is not None:
            self._engine.set_filename(value)
            self._declare_stream_length()

    def _on_progressed(self, source, event):
        progress = self._engine.get_progress()
        if not progress - self.previous_progress == 1:
            self.emit("progressed", progress, progress * self._engine.get_duration())
            if progress >= 1:
                self._on_eos()
            self.previous_progress = progress

    def _on_eos(self):
        self.rewind_timer.stop()
        self.stop()
        self.emit("eos")

    def _declare_stream_length(self):
        self.emit("limit-declared", self._engine.get_duration())

    def _rewind_forward(self):
        self._move_forward(self.rewind_step)

    def _rewind_backward(self):
        self._move_backward(self.rewind_step)

    def _move_forward(self, step):
        try:
            to = min(self._engine.get_progress() +
                     step / self._engine.get_duration(), 1)
            self._engine.set_progress(to)
        except ZeroDivisionError:
            pass

    def _move_backward(self, step):
        try:
            to = max(self._engine.get_progress() -
                 step / self._engine.get_duration(), 0)
            self._engine.set_progress(to)
        except ZeroDivisionError:
            pass

    def _toggle_rewind(self, where):
        was_rewinding = self.rewind_timer.is_playing()
        if was_rewinding:
            self.rewind_timer.stop()
        if not was_rewinding or self.rewind_direction != where:
            if self.rewind_timer_handler is not None:
                self.rewind_timer.disconnect(self.rewind_timer_handler)
            self.rewind_timer_handler = \
                self.rewind_timer.connect("completed", lambda *_: where())
            self.rewind_timer.start()
        self.rewind_direction = where

    def get_duration(self):
        """
        Get duration of the media stream in seconds.

        :return: duration, integer.
        """
        return self._engine.get_duration()

    def move_to(self, position):
        """
        Move to the given position.

        :param position: normalized value between 0 and 1.
        """
        self._engine.set_progress(position)

    def get_elapsed_time(self):
        """
        Get media stream elapsed time in seconds.

        :return: elapsed time, float.
        """
        return self._engine.get_duration() * self._engine.get_progress()

    def play(self):
        """
        Start playing the media stream.
        """
        self.stop_rewind()
        self._engine.set_playing(True)
        self.emit("started-playing")

    def stop(self):
        """
        Stop playing the media stream and move to the beginning.
        """
        self.stop_rewind()
        self._engine.set_playing(False)
        self._engine.set_progress(0)

    def pause(self):
        """
        Pause playing of the media stream.
        """
        self.stop_rewind()
        self._engine.set_playing(False)

    def is_playing(self):
        """
        Return the status of the media stream.

        :return: boolean.
        """
        return self._engine.get_playing()

    def set_volume(self, value):
        """
        Set volume of the media stream.

        :param value: normalized volume value between 0 and 1.
        """
        self._engine.set_audio_volume(value)

    def skip_forward(self):
        """
        Skip the media stream forward by the skip step.
        """
        self._move_forward(self.skip_step)

    def skip_backward(self):
        """
        Skip the media stream backward by the skip step.
        """
        self._move_backward(self.skip_step)

    def toggle_rewind_forward(self):
        """
        Start or stop rewind the media stream forward.
        """
        self._toggle_rewind(self._rewind_forward)

    def toggle_rewind_backward(self):
        """
        Start or stop rewind the media stream backward.
        """
        self._toggle_rewind(self._rewind_backward)

    def increase_volume(self):
        """
        Increase volume of the media stream by the volume step.
        """
        self.volume = min(self.volume + self.volume_step, 1)
        self._engine.set_audio_volume(self.volume)
        pisak.config['sound_effects_volume'] = str(int(self.volume * 100))

    def decrease_volume(self):
        """
        Decrease volume of the media stream by the volume step.
        """
        self.volume = max(self.volume - self.volume_step, 0)
        self._engine.set_audio_volume(self.volume)
        pisak.config['sound_effects_volume'] = str(int(self.volume * 100))

    def stop_rewind(self):
        """
        Stop any on-going process of media stream rewinding.
        """
        if self.rewind_timer.is_playing():
            self.rewind_timer.stop()


class AudioPlayback(MediaPlayback):
    """
    Tool for controlling playback of audio stream.
    """
    __gtype_name__ = "PisakAudioPlayback"

    def __init__(self):
        super().__init__()
        self.engine  = ClutterGst.VideoTexture()


class VideoPlayback(MediaPlayback):
    """
    Tool for controlling playback of video stream. Out of order, so far.
    """
    __gtype_name__ = "PisakVideoPlayback"

    def __init__(self):
        super().__init__()

    def set_subtitle_from_file(self, path):
        """
        Set subtitle for the current video stream. Format
        of a subtitle file should be one of these: TXT.

        :param path: path to a file containing subtitle.
        """
        self._engine.set_subtitle_uri(path)

    def set_subtitle_font(self, font):
        """
        Set font of a subtitle.

        :param font: font of a subtitle.
        """
        self._engine.set_subtitle_font_name(font)
