"""
Module contains all kinds of widgets to be used by any Pisak application.
"""
import math
import random
import time
import os

import cairo
from gi.repository import Clutter, Mx, GObject, Rsvg, Cogl, GdkPixbuf, Pango

import pisak
from pisak import res, logger, unit, properties, scanning, configurator, \
    utils, media, style, layout, svg, sound_effects
from pisak.res import colors

_LOG = logger.get_logger(__name__)


class Date(Mx.Label):
    """
    Display today date.
    """
    __gtype_name__ = "PisakDate"

    def __init__(self):
        today = "DATA:   " + time.strftime("%d-%m-%Y")
        self.set_text(today)


class PisakLogo(Mx.Image, configurator.Configurable):
    """
    Widget displaying PISAK project logo.
    """
    __gtype_name__ = "PisakLogo"

    LOGO_PATH = res.get("logo_pisak.png")

    def __init__(self):
        super().__init__()
        self.set_from_file(self.LOGO_PATH)
        self.apply_props()


class Frame(Mx.Frame):
    """
    Generic Pisak frame widget for visual purposes.
    """
    __gtype_name__ = "PisakFrame"

    def __init__(self):
        super().__init__()
        self.set_x_expand(True)
        self.set_y_expand(True)


class Playlist(Mx.ScrollView, properties.PropertyAdapter,
               configurator.Configurable):
    """
    Widget displaying scrollable list of buttons, each representing
    one media item.
    """
    __gtype_name__ = "PisakPlaylist"
    __gproperties__ = {
        "data-source": (
            GObject.GObject.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "playback": (
            media.MediaPlayback.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "visual": (
            Mx.Image.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "info-display": (
            GObject.GObject.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "ratio_width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio_height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.data_source = None
        self.playback = None
        self.info_display = None
        self.visual = None
        self.items = []
        self.idx = 0
        self.random_order = False
        self.looped = False
        self.apply_props()
        self._create_box()

    @property
    def ratio_width(self):
        return self._ratio_width

    @ratio_width.setter
    def ratio_width(self, value):
        self._ratio_width = value
        self.set_width(unit.w(value))

    @property
    def ratio_height(self):
        return self._ratio_height

    @ratio_height.setter
    def ratio_height(self, value):
        self._ratio_height = value
        self.set_height(unit.h(value))

    @property
    def playback(self):
        return self._playback

    @playback.setter
    def playback(self, value):
        self._playback = value
        if value is not None:
            value.connect("eos", lambda *_: self._next())
            if len(self.items) > 0:
                value.filename = self.items[0].path

    @property
    def info_display(self):
        return self._info_display

    @info_display.setter
    def info_display(self, value):
        self._info_display = value
        if value is not None:
            value.get_clutter_text().set_line_alignment(1)

    @property
    def data_source(self):
        return self._data_source

    @data_source.setter
    def data_source(self, value):
        self._data_source = value
        if value is not None:
            value.connect("data-is-ready", lambda *_: self._generate_content())

    @property
    def visual(self):
        return self._visual

    @visual.setter
    def visual(self, value):
        self._visual = value

    def _create_box(self):
        self.box = Mx.BoxLayout()
        self.box.set_orientation(Mx.Orientation.VERTICAL)
        self.box.set_scroll_to_focused(True)
        self.add_actor(self.box)

    def _generate_content(self):
        self._clean_old()
        self.items = self.data_source.get_all_items()
        for pos, item in enumerate(self.items):
            if pos == len(self.items) - 1:
                item.accept_focus(Mx.FocusHint.LAST)
            else:
                item.accept_focus(Mx.FocusHint.FIRST)
            self.box.add_actor(item, pos)
            item.connect("clicked", lambda src, item:
            self._play_item(item), item)
        if len(self.items) > 0:
            self.move_focus()

    def _clean_old(self):
        if self.is_playing():
            self.stop()
        self.idx = 0
        self.box.unparent()
        self.box.destroy()
        self._create_box()

    def _update_visualization(self):
        if self.visual is not None:
            if len(self.items) > 0:
                if hasattr(self.items[self.idx], "visual_path") and \
                                self.items[self.idx].visual_path is \
                                not None:
                    self.visual.set_from_file(self.items[self.idx].visual_path)
                    return
            self.visual.clear()

    def _update_info_display(self):
        if self.info_display is not None:
            if len(self.items) > 0:
                item = self.items[self.idx]
                if hasattr(item, "info") and item.info is not None:
                    self.info_display.set_text("\n".join(item.info))
                    return
            self.info_display.set_text("")

    def _next(self):
        self.playback.stop()
        self.items[self.idx].untoggle()
        if self.random_order is True:
            avalaible = list(range(len(self.items)))
            avalaible.remove(self.idx)
            self.idx = random.choice(avalaible)
            self.move_focus(self.items[self.idx],
                            Mx.FocusDirection.NEXT, and_play=True)
        else:
            self.idx = (self.idx + 1) % len(self.items)
            if self.idx == 0 and self.looped is False:
                self.stop()
            else:
                self.move_focus(self.items[self.idx],
                                Mx.FocusDirection.NEXT, and_play=True)

    def _play_item(self, item):
        self.items[self.idx].untoggle()
        self.idx = self.items.index(item)
        self.move_focus(and_play=True)

    def stop(self):
        """
        Stop playing the current item. Standby on the first item.
        """
        if len(self.items) > self.idx:
            if self.idx != 0:
                self.items[self.idx].untoggle()
                self.idx = 0
            self.playback.stop()
            self.items[self.idx].toggle()
            self.items[self.idx].move_focus(Mx.FocusDirection.NEXT,
                                            self.items[self.idx])
        if len(self.items) > 1:
            self.items[1].move_focus(Mx.FocusDirection.PREVIOUS,
                                     self.items[self.idx])

    def pause(self):
        """
        Pause playing of the current item. Standby on it.
        """
        self.playback.pause()

    def play(self):
        """
        Play the current item.
        """
        self.playback.play()

    def move_focus(self, previous=None, direction=None,
                   and_play=False):
        """
        Move focus to the current item and play it if ordered so.
        """
        self.items[self.idx].toggle()
        self._update_visualization()
        self._update_info_display()
        if direction and previous:
            self.items[self.idx].move_focus(direction, previous)
            if self.items.index(previous) == 0 and \
                            self.idx == len(self.items) - 1:
                self.items[self.idx - 1].move_focus(direction,
                                                    self.items[self.idx])
                self.items[self.idx - 2].move_focus(direction,
                                                    self.items[self.idx - 1])
                self.items[self.idx - 1].move_focus(Mx.FocusDirection.NEXT,
                                                    self.items[self.idx - 2])
            elif self.items.index(previous) == len(self.items) - 1 and \
                            self.idx == 0:
                self.items[self.idx + 1].move_focus(direction,
                                                    self.items[self.idx])
                self.items[self.idx + 2].move_focus(direction,
                                                    self.items[self.idx + 1])
                self.items[self.idx + 1].move_focus(Mx.FocusDirection.PREVIOUS,
                                                    self.items[self.idx + 2])
        if self.playback is not None:
            if self.items[self.idx].path != self.playback.filename:
                self.playback.filename = self.items[self.idx].path
            if and_play:
                self.play()

    def move_next(self):
        """
        Move to the next item.
        """
        was_playing = self.is_playing()
        self.playback.stop()
        item = self.items[self.idx]
        item.untoggle()
        self.idx = (self.idx + 1) % len(self.items)
        self.move_focus(item, Mx.FocusDirection.NEXT, was_playing)

    def move_previous(self):
        """
        Move to the previous item.
        """
        was_playing = self.is_playing()
        self.playback.stop()
        item = self.items[self.idx]
        item.untoggle()
        self.idx = (self.idx - 1) % len(self.items)
        self.move_focus(item, Mx.FocusDirection.PREVIOUS, was_playing)

    def is_playing(self):
        """
        Check if the current item is playing right now.
        """
        return self.playback.is_playing()


class TileContainer(object):
    """
    Base utility class for objects containing tiles that defines parameters
    needed to specify their appereance and behaviour.
    """

    @property
    def tile_ratio_height(self):
        return self._tile_ratio_height

    @tile_ratio_height.setter
    def tile_ratio_height(self, value):
        self._tile_ratio_height = value

    @property
    def tile_ratio_width(self):
        return self._tile_ratio_width

    @tile_ratio_width.setter
    def tile_ratio_width(self, value):
        self._tile_ratio_width = value

    @property
    def tile_ratio_spacing(self):
        return self._tile_ratio_spacing

    @tile_ratio_spacing.setter
    def tile_ratio_spacing(self, value):
        self._tile_ratio_spacing = value

    @property
    def tile_preview_ratio_height(self):
        return self._tile_preview_ratio_height

    @tile_preview_ratio_height.setter
    def tile_preview_ratio_height(self, value):
        self._tile_preview_ratio_height = value

    @property
    def tile_preview_ratio_width(self):
        return self._tile_preview_ratio_width

    @tile_preview_ratio_width.setter
    def tile_preview_ratio_width(self, value):
        self._tile_preview_ratio_width = value


class DialogWindow(layout.Box, configurator.Configurable):
    """
    Base class for different kinds of dialog windows for purposes of
    displaying informations for user or
    management of loading and saving content to the file system.
    """
    __gtype_name__ = "PisakDialogWindow"
    __gproperties__ = {
        "background_scene": (
            scanning.Group.__gtype__,
            "background scene",
            "scene to show pop up on",
            GObject.PARAM_READWRITE),
        "target": (
            Clutter.Actor.__gtype__,
            "target",
            "id of target",
            GObject.PARAM_READWRITE),
        "row_count": (
            GObject.TYPE_INT64, "number of rows",
            "number of rows with buttons", 0, 10, 3,
            GObject.PARAM_READWRITE),
        "column_count": (
            GObject.TYPE_INT64, "number of columns",
            "number of coolumns with buttons", 0, 10, 3,
            GObject.PARAM_READWRITE),
        "tile_ratio_width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "tile_ratio_height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.background_scene = None
        self.target = None
        self.row_count = 3
        self.column_count = 3
        self.tile_ratio_height = 0.08
        self.tile_ratio_width = 0.08
        self.continue_button_label = "KONTYNUUJ"
        self.exit_button_label = "WYJDŹ"

        self._prev_content = None
        self._middleware = None

        self.apply_props()

    @property
    def tile_ratio_width(self):
        return self._tile_ratio_width

    @tile_ratio_width.setter
    def tile_ratio_width(self, value):
        self._tile_ratio_width = value

    @property
    def tile_ratio_height(self):
        return self._tile_ratio_height

    @tile_ratio_height.setter
    def tile_ratio_height(self, value):
        self._tile_ratio_height = value

    @property
    def row_count(self):
        return self._row_count

    @row_count.setter
    def row_count(self, value):
        self._row_count = value

    @property
    def column_count(self):
        return self._column_count

    @column_count.setter
    def column_count(self, value):
        self._column_count = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def background_scene(self):
        return self._background_scene

    @background_scene.setter
    def background_scene(self, value):
        self._background_scene = value

    def on_screen(self, message, items=None):
        """
        Put the dialog window onto the screen. Generate content.
        If this is the case, start scanning it.
        """
        self.background_scanning_group = self.get_parent()
        self.stage = self.background_scene.get_stage()
        self.stage.add_child(self.background_scanning_group)
        self.space = self.get_children()[1]
        self.header = self.get_children()[0]
        self.header.set_text(message)
        self._generate_content(items)
        self.background_scanning_group.suppress_collapse_select_on_init = True
        pisak.app.window.pending_group = self.background_scanning_group

        self._middleware = pisak.app.window.input_group.middleware
        if self._middleware == "sprite":
            self._prev_content = pisak.app.window.input_group.content
            pisak.app.window.input_group.stop_middleware()
            pisak.app.window.input_group.load_content(self.background_scanning_group)

    def _generate_content(self, items=None):
        raise NotImplementedError

    def _close(self, source=None):
        if self._middleware == "sprite":
            pisak.app.window.input_group.stop_middleware()

        self.space.remove_all_children()
        self.stage.remove_child(self.background_scanning_group)
        pisak.app.window.pending_group = self.background_scene

        if self._middleware == "sprite":
            pisak.app.window.input_group.load_content(self._prev_content)


class ButtonSource(object):
    """
    Interface of the object that can produce descriptions
    of the multiple PisakButtons.
    """

    def get_buttons_descriptor(self):
        """
        Return list with descriptions of avalaible buttons.
        """
        raise NotImplementedError


class ButtonMenu(layout.Box, configurator.Configurable):
    """
    Widget arranging supplied PisakButton instances in row and columns
    and connect signals to them.
    """
    __gtype_name__ = "PisakButtonMenu"

    __gproperties__ = {
        "button_source": (GObject.GObject.__gtype__,
                          "", "", GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.buttons = []
        self.button_source = None
        self.apply_props()

    @property
    def button_source(self):
        return self._button_source

    @button_source.setter
    def button_source(self, value):
        self._button_source = value
        if value is not None:
            self.arrange_buttons()

    def arrange_buttons(self):
        if self.button_source is not None:
            descs = self.button_source.get_buttons_descriptor()
            count = len(descs)
            columns = math.ceil(math.sqrt(count))
            rows = columns - ((columns ** 2 - count) // columns)
            width = (self.get_width() - (columns - 1) * self.spacing) / columns
            height = (self.get_height() - (rows - 1) * self.spacing) / rows
            for idx in range(columns * rows):
                if idx % columns == 0:
                    row = layout.Box()
                    row.spacing = self.spacing
                    self.add_child(row)
                if idx >= count:
                    filler = Clutter.Actor()
                    row.add_child(filler)
                    filler.set_width(width)
                    filler.set_height(height)
                else:
                    desc = descs[idx]
                    button = Button()
                    button.set_width(width)
                    button.set_height(height)
                    button.set_x_align(Clutter.ActorAlign.START)
                    button.set_style_class(desc["style_class"])
                    button.icon_size = desc["icon_size"]
                    button.text = desc["label"]
                    button.set_label(desc["label"])
                    button.icon_name = desc["icon_name"]
                    button.connect("clicked", self.button_source.run_app, desc["exec_path"])
                    row.add_child(button)


class Timer(object):
    """
    Base class for custom stopwatch-like objects that can measure
    time progress.
    """

    def __init__(self):
        self._engine = Clutter.Timeline.new(1000)
        self._engine.set_repeat_count(-1)
        self._engine.connect("completed", self._update)

    def pause(self):
        """
        Pause the timer on the current time frame.
        """
        self._engine.pause()

    def start(self):
        """
        Make the timer running.
        """
        self._engine.start()

    def stop(self):
        """
        Stop the timer.
        """
        self._engine.stop()

    def _update(self):
        raise NotImplementedError


class Clock(layout.Bin, Timer, configurator.Configurable, style.StylableContainer):
    """
    Widget displaying the passage of time in the form of a CSS-stylable string.
    """
    __gtype_name__ = "PisakClock"
    __gproperties__ = {
        "direction": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE),
        "delimiter": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE),
        "measured-proccess": (
            GObject.GObject.__gtype__,
            "", "",
            GObject.PARAM_READWRITE),
        "style-class": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.value = 0
        self.measured_proccess = None
        self.direction = "forward"
        self.delimiter = ":"
        self._init_display()
        self.prepare_style()

    @property
    def style_class(self):
        return self._style_class

    @style_class.setter
    def style_class(self, value):
        self._style_class = value

    @property
    def delimiter(self):
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value):
        self._delimiter = value

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value

    @property
    def measured_proccess(self):
        return self._measured_proccess

    @measured_proccess.setter
    def measured_proccess(self, value):
        self._measured_proccess = value
        if value is not None:
            value.connect("progressed", self._supply_value)

    def _init_display(self):
        self.display = Mx.Label()
        self.display.set_style_class("PisakClock")
        self.add_child(self.display)
        self._update_display()

    def _supply_value(self, source, ratio, secs):
        self.value = math.floor(secs)  # int representing seconds
        self._update_display()

    def _update(self, source, event):
        if self.direction == "forward":
            self.value += 1
        elif self.direction == "backward":
            if self.value >= 1:
                self.value -= 1
                if self.value == 0:
                    self.stop()
        self._update_display()

    def _update_display(self):
        if self.get_parent() is not None:
            self.display.set_text(self._value_to_string())

    def _value_to_string(self):
        """
        Converts seconds value integer to the string in the format of hh:mm:ss or,
        if hours value equals 0, mm:ss.
        """
        hours = self.value // 3600
        minutes = self.value // 60 % 60
        seconds = self.value % 60
        time = [str(hours) if hours else None,
                ("0" if 0 < minutes < 10 else "") + str(minutes or "00"),
                ("0" if 0 < seconds < 10 else "") + str(seconds or "00")]
        return self.delimiter.join([i for i in time if i is not None])


class HiliteTool(Clutter.Actor):
    """
    Classes implementing HiliteTool interface can be used to add highlight to
    widgets which need to implement Scannable interface, but are not
    Stylable. Scannable widget should add HiliteTool instance as a descendant
    and call its methods to change highlight state.

    :see: :class:`pisak.libs.widgets.Aperture`
    """

    def turn_on(self):
        """
        Enable highlight.
        """
        raise NotImplementedError()

    def turn_off(self):
        """
        Disable highlight.
        """
        raise NotImplementedError()


class Aperture(
    HiliteTool,
    properties.PropertyAdapter,
    configurator.Configurable):
    """
    This actor draws a semi transparent cover with rectangular aperture in
    the center. It can be used to highlight another widget.
    """
    __gtype_name__ = "PisakAperture"
    __gproperties__ = {
        'cover': (GObject.TYPE_FLOAT, None, None,
                  0, 1, 0, GObject.PARAM_READWRITE),
        'r': (GObject.TYPE_FLOAT, None, None,
              0, 1, 0.51, GObject.PARAM_READWRITE),
        'g': (GObject.TYPE_FLOAT, None, None,
              0, 1, 0, GObject.PARAM_READWRITE),
        'b': (GObject.TYPE_FLOAT, None, None,
              0, 1, 1, GObject.PARAM_READWRITE)
    }

    COVER_OFF = 0.0

    COVER_ON = 0.2

    def __init__(self, r=0.51, g=0, b=1):
        super().__init__()
        self.set_x_expand(True)
        self.set_y_expand(True)
        self._init_content()
        self.r = r
        self.g = g
        self.b = b
        self.connect("notify::cover", lambda *_: self.canvas.invalidate())
        self.cover_transition = Clutter.PropertyTransition.new("cover")
        self.set_property("cover", 0)
        self.apply_props()

    @property
    def cover(self):
        """
        Specifies what portion of the actor should be covered. The value
        should range from 0 to 1. Covered area doesn't change linearly.
        """
        return self._cover

    @cover.setter
    def cover(self, value):
        self._cover = value

    @property
    def r(self):
        """
        Specifies amount(from 0 to 1) of red color in the cover.
        """
        return self._r

    @r.setter
    def r(self, value):
        self._r = float(value)

    @property
    def g(self):
        """
        Specifies amount(from 0 to 1) of green color in the cover.
        """
        return self._g

    @g.setter
    def g(self, value):
        self._g = float(value)

    @property
    def b(self):
        """
        Specifies amount(from 0 to 1) of blue color in the cover.
        """
        return self._b

    @b.setter
    def b(self, value):
        self._b = float(value)

    def set_cover(self, value):
        self.remove_transition("cover")
        self.cover_transition.set_from(self.get_property("cover"))
        self.cover_transition.set_to(value)
        self.cover_transition.set_duration(166)
        self.add_transition("cover", self.cover_transition)

    def _draw(self, canvas, context, w, h):
        context.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        context.rectangle(0, 0, w, h)
        context.set_source_rgba(self.r, self.g, self.b, 0.7)
        context.fill()
        context.set_operator(cairo.OPERATOR_CLEAR)
        a = 1 - self.get_property("cover")
        x, y = (0.5 - a / 2) * w, (0.5 - a / 2) * h
        rw, rh = a * w, a * h
        context.rectangle(x, y, rw, rh)
        context.fill()
        return True

    def _init_content(self):
        self.canvas = Clutter.Canvas()
        self.canvas.set_size(140, 140)
        self.canvas.connect("draw", self._draw)
        self.set_content(self.canvas)

    def turn_on(self):
        self.set_cover(self.COVER_ON)

    def turn_off(self):
        self.set_cover(self.COVER_OFF)


class PhotoTile(layout.Bin, properties.PropertyAdapter, scanning.Scannable,
                configurator.Configurable, style.StylableContainer):
    """
    Tile containing image and label that can be styled by CSS.
    This widget display a preview of a photo along with label. It can be
    used to display a grid of photo tiles.

    The style of PhotoTile elements be adjusted in CSS. The label is a
    "MxButton" element with "PisakPhotoTileLabel" class. The photo is
    "MxImage" element with no class set.
    """
    __gtype_name__ = "PisakPhotoTile"

    GTYPE_NAME = __gtype_name__
    """GType name"""

    __gsignals__ = {
        "clicked": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    __gproperties__ = {
        "preview_path": (
            GObject.TYPE_STRING,
            "path to preview photo",
            "path to preview photo displayed on a tile",
            "noop",
            GObject.PARAM_READWRITE),
        "preview_ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "preview_ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "scale_mode": (
            Mx.ImageScaleMode.__gtype__,
            "image scale mode", "scale mode", "crop",
            GObject.PARAM_READWRITE),
        "label_text": (
            GObject.TYPE_STRING,
            "label under the tile",
            "tile label text",
            "noop",
            GObject.PARAM_READWRITE),
        "hilite_tool": (
            HiliteTool.__gtype__,
            "actor to hilite", "hiliting tool",
            GObject.PARAM_READWRITE),
        "ratio_spacing": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "style-class": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE),
        "toggled": (
            GObject.TYPE_BOOLEAN,
            "", "", False,
            GObject.PARAM_READWRITE
        )
    }

    def __init__(self):
        super().__init__()

        self._make_pointer_reactive()
        self._init_box()
        self._init_elements()

        # container for tile extra specifications that can be applied
        # using the `adjust` method:
        self.spec = {}

        self.frame = None
        self.hilite_tool = None
        self.preview_loading_width = 300
        self.preview_loading_height = 300
        self.toggle_coeff = 0.6
        self._toggled = False
        self.scale_mode = Mx.ImageScaleMode.CROP

        self.prepare_style()

    @property
    def style_class(self):
        return self._style_class

    @style_class.setter
    def style_class(self, value):
        self._style_class = value

    @property
    def toggled(self):
        return self._toggled

    @toggled.setter
    def toggled(self, value):
        previous = self._toggled
        self._toggled = value
        if value != previous:
            if value:
                self._toggle()
            else:
                self._untoggle()

    @property
    def label_text(self):
        """
        Text on the photo label
        """
        return self.label.get_text()

    @label_text.setter
    def label_text(self, value):
        self.label.set_text(value)

    @property
    def preview_path(self):
        """
        Path to the preview photo
        """
        return self._preview_path

    @preview_path.setter
    def preview_path(self, value):
        self._preview_path = value
        width, height = self.preview.get_size()
        if width <= 1 or height <= 1:  # 1 x 1 as unrenderable picture size
            width, height = self.get_size()
        if width <= 1 or height <= 1:
            width = self.preview_loading_width
            height = self.preview_loading_height
        try:
            self.preview.set_from_file_at_size(value, width, height)
        except GObject.GError:
            self.preview.clear()

    @property
    def preview_ratio_width(self):
        """
        Screen-relative width
        """
        return self._preview_ratio_width

    @preview_ratio_width.setter
    def preview_ratio_width(self, value):
        self._preview_ratio_width = value
        self.preview.set_width(unit.w(value))

    @property
    def preview_ratio_height(self):
        """
        Screen-relative height
        """
        return self._preview_ratio_height

    @preview_ratio_height.setter
    def preview_ratio_height(self, value):
        self._preview_ratio_height = value
        self.preview.set_height(unit.h(value))

    @property
    def ratio_spacing(self):
        """
        Screen-relative spacing between photo and label
        """
        return self.box.ratio_spacing

    @ratio_spacing.setter
    def ratio_spacing(self, value):
        self.box.ratio_spacing = value

    @property
    def scale_mode(self):
        """
        Preview photo scale mode

        :see: :class:`gi.repository.Mx.Image`
        """
        return self.preview.get_scale_mode()

    @scale_mode.setter
    def scale_mode(self, value):
        self.preview.set_scale_mode(value)

    @property
    def hilite_tool(self):
        """
        Highlighting object.
        """
        return self._hilite_tool

    @hilite_tool.setter
    def hilite_tool(self, value):
        self._hilite_tool = value
        if value is not None:
            self.add_child(value)

    def _make_pointer_reactive(self):
        self.set_reactive(True)
        click_action = Clutter.ClickAction.new()
        click_action.connect("clicked", lambda *_: self.activate())
        self.add_action(click_action)
        self.connect("clicked", self._play_selection_sound)
        self.connect("enter-event", lambda *_: self.enable_hilite())
        self.connect("leave-event", lambda *_: self.disable_hilite())

    def _init_box(self):
        self.box = layout.Box()
        self.box.orientation = Clutter.Orientation.VERTICAL
        self.add_child(self.box)

    def _init_elements(self):
        self.preview = Mx.Image()
        self.preview.set_allow_upscale(True)
        self.box.add_child(self.preview)
        self.label = Mx.Label()
        self.label.set_style_class("PisakPhotoTileLabel")
        self.box.add_child(self.label)

    def _play_selection_sound(self, source):
        if pisak.app.window.input_group.middleware != "scanning":
            pisak.app.play_sound_effect('selection')

    def _toggle(self):
        for element in self.get_children():
            element.set_size(*[dim * self.toggle_coeff for dim in element.get_size()])

    def _untoggle(self):
        for element in self.get_children():
            element.set_size(*[dim / self.toggle_coeff for dim in element.get_size()])

    def add_frame(self, frame):
        """
        Add tile frame for extra visual effects.

        :param frame: tile frame widget
        """
        self.frame = frame
        self.add_child(frame)

    def activate(self):
        self.emit("clicked")

    def enable_hilite(self):
        if self.hilite_tool is not None:
            self.hilite_tool.r, self.hilite_tool.g, self.hilite_tool.b = \
                utils.convert_color(colors.PURPLE)[:-1]
            self.hilite_tool.turn_on()

    def disable_hilite(self):
        if self.hilite_tool is not None:
            self.hilite_tool.turn_off()

    def enable_lag_hilite(self):
        if self.hilite_tool is not None:
            self.hilite_tool.r, self.hilite_tool.g, self.hilite_tool.b = \
                utils.convert_color(colors.CYAN)[:-1]
            self.hilite_tool.turn_on()

    def disable_lag_hilite(self):
        if self.hilite_tool is not None:
            self.hilite_tool.turn_off()

    def enable_scanned(self):
        # TODO: add scanned highlight
        pass

    def disable_scanned(self):
        # TODO: add scanned highlight
        pass

    def is_disabled(self):
        return False

    def adjust(self):
        """
        Adjust the tile using any specifications stored in the
        `spec` dictionary. Caution is advised when using this method
        because as a result each item from the `spec` will become
        an attribute of `self`, overwriting any existing ones.
        """
        for key, value in self.spec.items():
            setattr(self, key, value)


class Slider(Mx.Slider, properties.PropertyAdapter, configurator.Configurable,
             style.StylableContainer):
    """
    Widget indicating a range of content being displayed, consists of bar with
    handle moving back and forth on top of it.
    """
    __gtype_name__ = "PisakSlider"
    __gproperties__ = {
        "value-transition-duration": (
            GObject.TYPE_INT64, "transition duration",
            "duration of value transition in msc", 0,
            GObject.G_MAXUINT, 1000, GObject.PARAM_READWRITE),
        "followed-object": (
            Clutter.Actor.__gtype__,
            "", "", GObject.PARAM_READWRITE)
    }

    def __init__(self):
        self.value_transition = Clutter.PropertyTransition.new("value")
        self.value_transition_duration = 1000
        self.followed_object = None
        self.prepare_style()

    @property
    def followed_object(self):
        return self._followed_object

    @followed_object.setter
    def followed_object(self, value):
        self._followed_object = value
        if value is not None:
            value.connect("progressed", self._set_value)

    @property
    def value_transition_duration(self):
        return self.value_transition.get_duration()

    @value_transition_duration.setter
    def value_transition_duration(self, value):
        self.value_transition.set_duration(value)

    def _set_value(self, source, value, custom_step):
        self.value_transition.set_from(self.get_value())
        self.value_transition.set_to(value)
        self.remove_transition("value")
        self.add_transition("value", self.value_transition)


class ProgressBar(layout.Bin, properties.PropertyAdapter, configurator.Configurable,
                  style.StylableContainer):
    """
    Custom-drawn progress indicator. Progress bar can observe one object for
    progress. Observed object emits two types of signal: "limit-declared" and
    "progressed". The former signal is emitted to set maximal progress value,
    the latter one is emitted to set current progress.

    This widget is composed from MxProgressBar an MxLabel and can be styled
    in CSS.
    """
    __gtype_name__ = "PisakProgressBar"
    __gproperties__ = {
        "label": (
            Mx.Label.__gtype__,
            "", "", GObject.PARAM_READWRITE),
        "progress": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "progress_transition_duration": (
            GObject.TYPE_INT64, "transition duration",
            "duration of progress transition in msc", 0,
            GObject.G_MAXUINT, 1000, GObject.PARAM_READWRITE),
        "label_ratio_x_offset": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "counter_limit": (
            GObject.TYPE_INT64, "counter limit",
            "max counter value", 0, GObject.G_MAXUINT,
            10, GObject.PARAM_READWRITE),
        "followed-object": (
            GObject.GObject.__gtype__,
            "", "", GObject.PARAM_READWRITE),
        "style-class": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self._init_bar()
        self.label = None
        self.step = None
        self.label_ratio_x_offset = None
        self.counter_limit = None
        self.progress_transition = Clutter.PropertyTransition.new("progress")
        self.progress_transition_duration = 1000
        self.progress_transition.connect("stopped", self._update_label)
        self.connect("notify::width", self._allocate_label)
        self.prepare_style()

    @property
    def style_class(self):
        return self._style_class

    @style_class.setter
    def style_class(self, value):
        self._style_class = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        if value is not None:
            value.set_y_expand(True)
            value.set_y_align(Clutter.ActorAlign.CENTER)
            self.insert_child_above(value, None)

    @property
    def followed_object(self):
        """
        Object observed by the progressbar.
        """
        return self._related_object

    @followed_object.setter
    def followed_object(self, value):
        self._followed_object = value
        if value is not None:
            value.connect("limit-declared", self._set_counter_limit)
            value.connect("progressed", self._set_progress)

    @property
    def counter_limit(self):
        """
        Maximal progress value.
        """
        return self._counter_limit

    @counter_limit.setter
    def counter_limit(self, value):
        self._counter_limit = value
        if value is not None:
            self.step = int(self.progress * value)
        self._update_label()

    @property
    def progress(self):
        """
        Progressbar value.
        """
        return self.bar.get_progress()

    @progress.setter
    def progress(self, value):
        self.progress_transition.set_from(self.progress)
        self.progress_transition.set_to(value)
        self.bar.remove_transition("progress")
        self.bar.add_transition("progress", self.progress_transition)
        if self.counter_limit is not None:
            self.step = int(value * self.counter_limit)

    @property
    def progress_transition_duration(self):
        """
        Duration of animation in milliseconds.
        """
        return self.progress_transition.get_duration()

    @progress_transition_duration.setter
    def progress_transition_duration(self, value):
        self.progress_transition.set_duration(value)

    @property
    def label_ratio_x_offset(self):
        """
        Horizontal offset of label relative to progressbar width
        """
        return self._label_ratio_x_offset

    @label_ratio_x_offset.setter
    def label_ratio_x_offset(self, value):
        self._label_ratio_x_offset = value
        self._allocate_label()

    def _init_bar(self):
        self.bar = Mx.ProgressBar()
        self.bar.set_x_expand(True)
        self.bar.set_y_expand(True)
        self.insert_child_below(self.bar, None)

    def _allocate_label(self, *args):
        if self.label is not None:
            if self.get_width() and self.label_ratio_x_offset is not None:
                px_x_offset = self.label_ratio_x_offset * self.get_width()
                self.label.set_x(px_x_offset)

    def _set_counter_limit(self, source, limit):
        self.counter_limit = limit

    def _set_progress(self, source, progress, custom_step):
        if self.get_parent() is not None:
            self.progress = progress
            self.step = custom_step

    def _update_label(self, *args):
        if self.label is not None:
            new_text = " / ".join([str(self.step),
                                   str(self.counter_limit)])
            self.label.set_text(new_text)


class Header(Clutter.Actor, properties.PropertyAdapter, configurator.Configurable,
             style.StylableContainer):
    """
    Widget for displaying header being a svg icon.
    """
    __gtype_name__ = "PisakMenuHeader"
    __gproperties__ = {
        "name": (
            GObject.TYPE_STRING, None, None, "",
            GObject.PARAM_READWRITE),
        "ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0,
            1., 0, GObject.PARAM_READWRITE),
        "color": (
            GObject.TYPE_STRING, None, None, "",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.svg = None
        self._color = None
        self._canvas = Clutter.Canvas()
        self.set_content(self._canvas)
        self._canvas.set_size(20, 20)
        self._canvas.connect('draw', self._draw)
        self._canvas.invalidate()
        self.prepare_style()

    def _draw(self, canvas, context, w, h):
        if self.svg is None:
            return
        if self.color is not None:
            self.svg.change_color(self.color)
        handle, pixbuf = self.svg.get_handle(), self.svg.get_pixbuf()

        context.set_operator(cairo.OPERATOR_SOURCE)

        scale_w = w/pixbuf.get_width()
        scale_h = h/pixbuf.get_height()
        scale_ratio  = scale_w / scale_h
        if scale_ratio > 1:
            scale_w /= scale_ratio
        elif scale_ratio < 1:
            scale_h *= scale_ratio
        context.scale(scale_w, scale_h)

        handle.render_cairo(context)

    @property
    def ratio_width(self):
        """
        Screen-relative width.
        """
        return self._ratio_width

    @ratio_width.setter
    def ratio_width(self, value):
        self._ratio_width = value
        self.set_width(unit.w(value))
        self._load()

    @property
    def ratio_height(self):
        """
        Screen-relative height.
        """
        return self._ratio_height

    @ratio_height.setter
    def ratio_height(self, value):
        self._ratio_height = value
        self.set_height(unit.h(value))
        self._load()

    @property
    def color(self):
        """
        Color of the icon.
        """
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self._load()

    @property
    def name(self):
        """
        Icon name to be found in res folder.
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        try:
            self.svg = svg.PisakSVG(value)
            self._load()
        except FileNotFoundError as message:
            _LOG.warning(message)

    def _load(self):
        self._canvas.set_size(self.get_width(), self.get_height())
        self._canvas.invalidate()


class Button(Mx.Button, properties.PropertyAdapter, scanning.StylableScannable,
             configurator.Configurable, style.StylableContainer):
    """
    This is extension of MxButton for Pisak purposes. It implements
    some additional features when compared to MxButton:

    - button icon changes along with CSS pseudoclass,
    - it implements Scannable interface and is recognized by scanning groups,
    - it allows adjusting space between icon and text.
    - button has special highlight feedback when it is selected
    """
    __gtype_name__ = "PisakButton"

    __gproperties__ = {
        "ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0,
            1., 0, GObject.PARAM_READWRITE),
        "text": (
            GObject.TYPE_STRING, "label default text",
            "text displayed on the button", "noop",
            GObject.PARAM_READWRITE),
        "alternative_text": (
            GObject.TYPE_STRING,
            "alternative label text",
            "alternative text displayed on the button",
            "?", GObject.PARAM_READWRITE),
        "icon_name": (
            GObject.TYPE_STRING, "blank",
            "name of the icon displayed on the button",
            "blank", GObject.PARAM_READWRITE),
        "icon_size": (
            GObject.TYPE_INT64, "", "", 0, 1000, 50,
            GObject.PARAM_READWRITE),
        "toggled_icon_name": (
            GObject.TYPE_STRING, "toggled state icon",
            "name of the icon displayed in the toggled state",
            "toggled state icon name", GObject.PARAM_READWRITE),
        "spacing": (
            GObject.TYPE_INT64, "space between icon and text",
            "space between icon and text", 0, 1000, 100,
            GObject.PARAM_READWRITE),
        "on_select_hilite_duration": (
            GObject.TYPE_UINT, "hilite duration",
            "duration of hilite in msc",
            0, GObject.G_MAXUINT, 1000,
            GObject.PARAM_READWRITE),
        "related_object": (
            Clutter.Actor.__gtype__,
            "related object",
            "object that button has an impact on",
            GObject.PARAM_READWRITE),
        "custom_padding": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE),
        "scanning_pauser": (
            GObject.TYPE_BOOLEAN,
            "", "", False,
            GObject.PARAM_READWRITE),
        "disabled_when": (
            GObject.TYPE_STRING, "", "", "",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.box = None
        self.sounds = {}
        self._prepare_label()
        self.on_select_hilite_duration = None
        self.related_object = None
        self.scanning_pauser = False
        self.current_icon_name = None
        self.toggled_icon_name = None
        self.space = None
        self._padding = None
        self.custom_padding = None
        self.svg = None
        self.icon_name = None
        self.disabled = False
        self.disabled_when = None
        self.content_offset = 26
        self._connect_signals()
        self.prepare_style()

    def _prepare_label(self):
        self.clutter_text = [child for child in
                             self.get_children()[0].get_children()
                             if isinstance(child, Clutter.Text)][0]
        self.clutter_text.connect("notify::color",
                                  self._change_icon_style)
        self.clutter_text.set_property("ellipsize", 0)

    def _connect_signals(self):
        self.connect("clicked", self._play_selection_sound)
        self.connect("notify::text", self._set_initial_label)
        self.connect("clicked", self.on_click_activate)
        self.connect("notify::style-pseudo-class",
                     self._on_style_pseudo_class_change)
        self.connect("notify::size", lambda *args: self._rescale_icon())
        self.connect("notify::mapped", self.set_space)
        self.connect("notify::mapped", self._change_icon_style)
        self.set_reactive(True)

    def _play_selection_sound(self, source):
        if pisak.app.window.input_group.middleware != "scanning":
            pisak.app.play_sound_effect('selection')

    @property
    def disabled_when(self):
        """
        One can mark some highly specific conditions that should
        make the button disabled. Conditions must be in a format
        of comma separated string. Currently supported conditions are:
        scanning_off - when the scanning mode is off
        """
        return self._disabled_when

    @disabled_when.setter
    def disabled_when(self, value):
        self._disabled_when = value
        if value is not None:
            when = value.split(",")
            for cond in when:
                if cond.strip() == "scanning_off":
                    if pisak.app.window.input_group.middleware != "scanning":
                        self.set_disabled(True)
                        self.image.set_opacity(100)

    @property
    def scanning_pauser(self):
        return self._scanning_pauser

    @scanning_pauser.setter
    def scanning_pauser(self, value):
        self._scanning_pauser = value

    @property
    def related_object(self):
        return self._related_object

    @related_object.setter
    def related_object(self, value):
        self._related_object = value

    @property
    def ratio_width(self):
        """
        Screen-relative width
        """
        return self._ratio_width

    @ratio_width.setter
    def ratio_width(self, value):
        self._ratio_width = float(value)
        self.set_width(unit.w(self._ratio_width))

    @property
    def ratio_height(self):
        """
        Screen-relative height
        """
        return self._ratio_height

    @ratio_height.setter
    def ratio_height(self, value):
        self._ratio_height = float(value)
        self.set_height(unit.h(self._ratio_height))

    @property
    def text(self):
        """
        Button text.
        """
        return self._text

    @text.setter
    def text(self, value):
        self._text = str(value)
        self.sounds[self._text] = self.get_sound(self._text)

    @property
    def alternative_text(self):
        """
        Button text in switched state.

        :see: switch_label
        :see: set_default_label
        """
        return self._alternative_text

    @alternative_text.setter
    def alternative_text(self, value):
        self._alternative_text = str(value)
        self.sounds[self._alternative_text] = self.get_sound(
            self._alternative_text)
        
    def get_sound(self, name):
        sound = sound_effects.Sound(os.path.join(res.get('sounds'),
                                                 'scan.wav'))
        if name:
            fname = name.lower()
            fname = fname.replace(' ', '_').replace('\n', '_') + '.wav'
            fpath = os.path.join(res.get('sounds'), fname)
            if os.path.isfile(fpath):
                sound = sound_effects.Sound(fpath)
        return sound
        
    @property
    def current_icon_name(self):
        """
        Name of the currently displayed icon.
        """
        return self._current_icon_name

    @current_icon_name.setter
    def current_icon_name(self, value):
        self._current_icon_name = value
        if isinstance(value, str):
            if not self.box:
                self.custom_content()
            if len(value) > 0:
                self.load_icon()
                self.box.show()
            else:
                self.box.hide()

    @property
    def toggled_icon_name(self):
        """
        Name of icon in toggled state.
        """
        return self._toggled_icon_name

    @toggled_icon_name.setter
    def toggled_icon_name(self, value):
        self._toggled_icon_name = value
        self.sounds[value] = self.get_sound(value)

    @property
    def icon_name(self):
        """
        Name of the default icon on the button.
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, value):
        self._icon_name = value
        self.sounds[value] = self.get_sound(value)
        self.current_icon_name = value

    @property
    def icon_size(self):
        """
        Name of icon on the button
        """
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value):
        self._icon_size = int(value)

    @property
    def spacing(self):
        """
        Spacing between button label and icon.
        """
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = value

    @property
    def on_select_hilite_duration(self):
        """
        Duration of highlight when the button is selected.
        """
        return self._on_select_hilite_duration

    @on_select_hilite_duration.setter
    def on_select_hilite_duration(self, value):
        self._on_select_hilite_duration = value

    def _set_initial_label(self, source, spec):
        self.set_default_label()
        self.disconnect_by_func(self._set_initial_label)

    def set_default_label(self):
        """
        Restores default label

        :see: text
        :see: alternative_text
        """
        self.set_label(self.text)

    def set_space(self, *args):
        """
        Sets space between label and icon
        """
        try:
            if self.custom_padding:
                self._insert_padding()
            else:
                img_width = self.image.get_width()
                text_width = self.get_children()[0].get_children()[1].get_width()
                butt_width = self.get_width()
                self.space.set_width(
                    butt_width - img_width - text_width - self.content_offset)
        except AttributeError:
            pass

    @property
    def custom_padding(self):
        """
        Custom padding to be inserted into the button. Avalaible are 'right'
        and 'left'. Content will be automaticaly scaled.
        """
        return self._custom_padding

    @custom_padding.setter
    def custom_padding(self, value):
        self._custom_padding = value

    def _insert_padding(self):
        padding_ratio = 0.95
        original_box = self.get_children()[0]
        text_width = original_box.get_children()[1].get_width()
        img_width = self.image.get_width()
        button_width = self.get_width()
        empty_width = button_width - img_width - text_width - \
                      self.content_offset
        padding_width = empty_width * padding_ratio
        space_width = empty_width - padding_width
        if self.space:
            self.space.set_width(space_width)
        self._padding = Clutter.Actor()
        self._padding.set_width(padding_width)
        if self.custom_padding == "left":
            where = 0
        elif self.custom_padding == "right":
            where = -1
        original_box.add_actor(self._padding, where)

    def set_alternative_label(self):
        """
        Sets alternative label as current
        """
        self.set_label(self.alternative_text)

    def switch_label(self):
        """
        Switches between labels
        """
        current_label = self.get_label()
        if current_label in (self.alternative_text, None):
            self.set_default_label()
        elif current_label == self.text:
            self.set_alternative_label()

    def switch_icon(self):
        """
        Switches between icons
        """
        raise NotImplementedError

    def _on_style_pseudo_class_change(self, source, event):
        if self.style_pseudo_class_contains("toggled"):
            self.current_icon_name = self.toggled_icon_name
        if not self.style_pseudo_class_contains("toggled") and \
                        self.current_icon_name == self.toggled_icon_name:
            self.current_icon_name = self.icon_name
        self._change_icon_style()

    def custom_content(self):
        self.set_icon_visible(False)
        self.box = layout.Box()
        original_box = self.get_children()[0]
        text_content = self.clutter_text.get_text()
        if text_content.strip() == '':
            original_box.set_layout_manager(Clutter.BinLayout())
            original_box.add_actor(self.box, 1)
        else:
            original_box.add_actor(self.box, 1)
            self.space = Clutter.Actor()
            self.box.add_child(self.space)
        self.image = Mx.Image()
        self.image.set_transition_duration(0)
        self.image.set_scale_mode(1)  # 1 is FIT, 0 is None, 2 is CROP
        self.box.add_child(self.image)

    def _rescale_icon(self):
        icon_width_ratio = 0.8
        icon_size_ratio = 0.7
        icon_preffered_height = int(min(self.get_size()) * icon_size_ratio)
        if icon_preffered_height > 1:
            self.icon_size = icon_preffered_height
        if self.svg:
            if self.icon_size:
                self.image.set_size(self.icon_size * icon_width_ratio, self.icon_size)
            self.set_icon()

    def load_icon(self):
        self.load_svg()
        self._rescale_icon()
        if self.is_disabled():
            self.image.set_opacity(100)

    def load_svg(self):
        try:
            self.svg = svg.PisakSVG(self.current_icon_name)
        except FileNotFoundError as error:
            _LOG.warning(error)

    def set_icon_color(self, color='white'):
        self.svg.change_color(color)
        self.set_icon()

    def set_icon(self):
        pixbuf = self.svg.get_pixbuf()
        self.image.set_from_data(pixbuf.get_pixels(),
                                 Cogl.PixelFormat.RGBA_8888,
                                 pixbuf.get_width(),
                                 pixbuf.get_height(),
                                 pixbuf.get_rowstride())

    def _change_icon_style(self, *args):
        try:
            self.clutter_text.disconnect_by_func(self._change_icon_style)
        except TypeError:
            pass
        if not self.current_icon_name:
            return  # no icon so nothing to has its style changed
        try:
            color = self.clutter_text.get_color()
            self.set_icon_color('rgb({}, {}, {})'.format(color.red,
                                                         color.green,
                                                         color.blue))
        except AttributeError:
            msg = 'No icon for button {} or icon is not a svg.'
            _LOG.info(msg.format(self))

    def hilite_off(self):
        self.style_pseudo_class_remove("hover")

    def hilite_on(self):
        self.style_pseudo_class_add("hover")

    def on_select_hilite_off(self, token):
        if token == self.timeout_token:
            self.style_pseudo_class_remove("active")

    def on_click_activate(self, source):
        if self.on_select_hilite_duration:
            self.style_pseudo_class_add("active")
            self.timeout_token = object()
            Clutter.threads_add_timeout(0,
                                        self.on_select_hilite_duration,
                                        self.on_select_hilite_off,
                                        self.timeout_token)

    def activate(self):
        """
        Completion of scannable interafece.
        :see: Scannable
        """
        self.emit("clicked")

    def is_disabled(self):
        return self.get_disabled()

    def is_toggled(self):
        return self.style_pseudo_class_contains("toggled")

    def is_working(self):
        return self.style_pseudo_class_contains("working")

    def toggle(self):
        """
        Set the toggled state of the Button.
        Add 'toggled' pseudo class to style.
        """
        self.style_pseudo_class_add("toggled")

    def untoggle(self):
        """
        Set the un-toggled state of the Button.
        Remove 'toggled' pseudo class from style.
        """
        self.style_pseudo_class_remove("toggled")

    def set_working(self):
        """
        Set working state of the button.
        Add 'working' pseudo class to style.
        """
        self.style_pseudo_class_add("working")

    def set_unworking(self):
        """
        Set non-working state of the button.
        Remove 'working' pseudo class from style.
        """
        self.style_pseudo_class_remove("working")


class BackgroundPattern(layout.Bin):
    """
    This simple actor serves as standard background for Pisak application.
    It is based on dynamically generated background pattern.
    It inherites from :class:`pisak.layout.Bin` for some convenience purposes.
    """
    __gtype_name__ = "PisakBackgroundPattern"
    __gproperties__ = {
        "rgba": (
            GObject.TYPE_STRING,
            "color of fence",
            "color of fence pattern as rgba string value",
            "", GObject.PARAM_READWRITE),
        "pattern": (
            GObject.TYPE_STRING,
            "", "", "", GObject.PARAM_READWRITE),
    }

    def __init__(self):
        super().__init__()
        self._rgba = [0, 0, 0, 0.15]
        self._pattern = "fence"
        self.canvas_handler = None
        self.background_image = Clutter.Canvas()
        self.set_content(self.background_image)
        self.background_image.set_size(unit.mm(2), unit.mm(2))
        self.background_image.connect("draw", self._draw)
        self.background_image.invalidate()
        self.connect("notify::background-color", lambda *_:
        self.background_image.invalidate)
        self.apply_props()

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        """
        Type of pattern to be drawn as background of an app. Avalaible:
        'fence' - default type, dense fence-like pattern of thin, slanted
        lines in the 'rgba' color, crossing each other at the right angle, on
        top of the plain background in the 'background-color';
        'gradient' - linear, horizontal gradient from 'rgba' color
        on both sides to the 'background-color' in the middle.

        :param value: name of the pattern as string

        See also:
        
        :see: :property:`pisak.widgets.BackgroundPattern.rgba`
        """
        self._pattern = value
        self.background_image.invalidate()

    @property
    def rgba(self):
        return self._rgba

    @rgba.setter
    def rgba(self, value):
        """
        Color of the background pattern.

        :param value: color as a string, in a format of comma separated
        four integer values, each corresponding to the amounts of,
        consecutively, red, green, blue and alpha channels
        in the resulting color. Given string is then converted to the list
        containing floating point values of the consecutive channels.
        """
        self._rgba = list(map(
            lambda string: float(string.strip())/255, value.split(",")))
        self.background_image.invalidate()

    def _draw(self, canvas, context, w, h):
        """
        General drawing method, called after the 'draw' signal is emitted by
        the canvas. Method itself calls one of the methods responsible for
        doing the custom type of drawing. Specific custom drawing method is
        picked if its name consists of '_draw' and the current pattern name,
        joined by a single underscore. For example, if the current 'pattern'
        property is 'fence' and method named '_draw_fence' is implemented then
        it will be called at some point from here.

        :param canvas: instance of canvas
        :param context: instance of cairo context
        :param w: width of canvas in pixels
        :param h: height of canvas in pixels
        """
        context.scale(w, h)
        context.set_operator(cairo.OPERATOR_SOURCE)
        if hasattr(self, "_draw_" + self.pattern):
            getattr(self, "_draw_" + self.pattern)(canvas, context, w, h)
        else:
            message = "Pattern {} is not avalaible or its painter is not implemented yet."
            _LOG.warning(message.format(self.pattern))
        return True

    def _draw_fence(self, canvas, context, w, h):
        """
        Draws specific fence-like pattern on the canvas. Method is
        called internally by the general drawing method if the 'pattern'
        property is set to 'fence'.

        :param canvas: instance of canvas
        :param context: instance of cairo context
        :param w: width of canvas in pixels
        :param h: height of canvas in pixels
        """
        self.set_content_repeat(Clutter.ContentRepeat.BOTH)
        self.set_content_scaling_filters(Clutter.ScalingFilter.TRILINEAR,
                                         Clutter.ScalingFilter.TRILINEAR)
        context.set_source_rgba(*utils.convert_color(
            self.get_background_color()))
        context.paint()
        context.set_line_width(0.05)
        context.set_source_rgba(*self.rgba)
        lines = [(0, 0, 1, 1), (0, 1, 1, 0)]
        for x1, y1, x2, y2 in lines:
            context.move_to(x1, y1)
            context.line_to(x2, y2)
            context.stroke()

    def _draw_gradient(self, canvas, context, w, h):
        """
        Draws specific linear-gradient pattern on the canvas. Method is
        called internally by the general drawing method if the 'pattern'
        property is set to 'gradient'.

        :param canvas: instance of canvas
        :param context: instance of cairo context
        :param w: width of canvas in pixels
        :param h: height of canvas in pixels
        """
        self.set_content_repeat(Clutter.ContentRepeat.NONE)
        self.set_content_scaling_filters(Clutter.ScalingFilter.LINEAR,
                                         Clutter.ScalingFilter.LINEAR)
        gradient = cairo.LinearGradient(0, 0, 1, 0)
        gradient.add_color_stop_rgba(0.1, *self.rgba)
        gradient.add_color_stop_rgba(0.5, *utils.convert_color(
            self.get_background_color()))
        gradient.add_color_stop_rgba(0.9, *self.rgba)
        context.set_source(gradient)
        context.paint()

class BacgroundFulfillment(Mx.Frame):
    """
    This is used only for the possibility to change background in css file.
    """

    __gtype_name__ = "PisakBackgroundFulfillment"
