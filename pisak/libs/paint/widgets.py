import os
import math

from gi.repository import GObject, Clutter
import cairo

import pisak
from pisak import res
from pisak.libs import widgets, layout, dirs, properties, utils, configurator


SAVE_FILE_BASENAME = "PISAK_paint_"

SAVE_DIR = dirs.get_user_dir("pictures")


class EaselTool(Clutter.Actor, properties.PropertyAdapter):
    """
    Base class for the easel tools.
    """
    __gproperties__ = {
        "step-duration": (
            GObject.TYPE_INT,
            "step duration",
            "duration in mscs",
            1, 10000, 100,
            GObject.PARAM_READWRITE),
        "step": (
            GObject.TYPE_FLOAT, None, None,
            0, 10000, 0, GObject.PARAM_READWRITE),
        "max-cycles": (
            GObject.TYPE_FLOAT, None, None,
            -1, 100, 0, GObject.PARAM_READWRITE),
        "line-width": (
            GObject.TYPE_FLOAT, None, None,
            0, 100, 0, GObject.PARAM_READWRITE),
        "line-color": (
            GObject.TYPE_STRING,
            "line color",
            "line color",
            " ",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.set_clip_to_allocation(True)
        self.canvas = Clutter.Canvas()
        self.set_content(self.canvas)
        self.line_rgba = ()
        self.click_handlers = []

    @property
    def step_duration(self):
        return self._step_duration

    @step_duration.setter
    def step_duration(self, value):
        self._step_duration = value

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value

    @property
    def max_cycles(self):
        return self._max_cycles

    @max_cycles.setter
    def max_cycles(self, value):
        self._max_cycles = value

    @property
    def line_width(self):
        return self._line_width

    @line_width.setter
    def line_width(self, value):
        self._line_width = value

    @property
    def line_color(self):
        return self._line_color

    @line_color.setter
    def line_color(self, value):
        self._line_color = value
        if value is not None:
            self.line_rgba = utils.convert_color(value)

    def _clear_canvas(self):
        try:
            self.canvas.disconnect_by_func(self._draw)
        except TypeError:
            pass
        self.canvas.connect("draw", self._draw_clear)
        self.canvas.invalidate()
        self.canvas.disconnect_by_func(self._draw_clear)
        self.canvas.connect("draw", self._draw)

    def _draw_clear(self, cnvs, ctxt, width, height):
        ctxt.set_operator(cairo.OPERATOR_SOURCE)
        ctxt.set_source_rgba(0, 0, 0, 0)
        ctxt.paint()
        return True

    def _draw(self, cnvs, ctxt, width, height):
        raise NotImplementedError

    def run(self):
        """
        Make the tool going.
        """
        raise NotImplementedError

    def kill(self):
        """
        Stop all the on-going activity and kill the tool.
        """
        raise NotImplementedError

    def on_user_click(self, source, event):
        """
        Public signal handler calling internally declared functions.
        """
        for handler in self.click_handlers:
            handler(source, event)


class Navigator(EaselTool, configurator.Configurable):
    """
    Easel tool, widget displaying straight, rotating line that indicates angle
    of the line to be drawn.
    """
    __gtype_name__ = "PisakPaintNavigator"
    __gsignals__ = {
        "angle-declared": (GObject.SIGNAL_RUN_FIRST,
                           None, (GObject.TYPE_FLOAT,)),
        "idle": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()
        self.max_cycles = 1
        self.step_duration = 50
        self.step = 0.007
        self.line_color = Clutter.Color.new(0, 0, 0, 255)
        self.line_width = 5
        self.click_handlers = [self._on_user_decision]
        self.apply_props()

    def run(self, from_x, from_y):
        """
        Turn on the navigator, begin line rotation.
        :param from_x: x coordinate of the navigator base point
        :param from_y: y coordinate of the navigator base point
        """
        self.angle = 0
        self.width, self.height = self.get_size()
        self.diagonal = (self.width**2 + self.height**2)**0.5
        self.canvas.set_size(self.width, self.height)
        self.canvas.connect("draw", self._draw)
        self.from_x = from_x
        self.from_y = from_y
        self.timer = Clutter.Timeline.new(self.step_duration)
        repeat_count = -1 if self.max_cycles == -1 else \
            self.max_cycles * 2 * math.pi / self.step
        self.timer.set_repeat_count(repeat_count)
        self.timer.connect("completed", self._update_navigator)
        self.timer.connect("stopped", self._on_user_idle)
        self.timer.start()

    def kill(self):
        """
        Stop all the on-going activities and kill the navigator.
        """
        self._clean_up()
        self.timer.stop()

    def _on_user_decision(self, source, event):
        self._clean_up()
        self.timer.stop()
        self.emit("angle-declared", self.angle)

    def _on_user_idle(self, source, event):
        self._clean_up()
        self.emit("idle")

    def _clean_up(self):
        self._clear_canvas()
        self.timer.disconnect_by_func(self._on_user_idle)
        self.timer.disconnect_by_func(self._update_navigator)
        self.canvas.disconnect_by_func(self._draw)

    def _update_navigator(self, event):
        self.angle += self.step
        self.canvas.invalidate()

    def _draw(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        ctxt.translate(self.from_x, self.from_y)
        ctxt.rotate(self.angle)
        ctxt.scale(self.diagonal/width, 1)
        ctxt.move_to(0, 0)
        ctxt.line_to(width, 0)
        ctxt.set_line_width(self.line_width)
        ctxt.set_source_rgba(*self.line_rgba)
        ctxt.stroke()
        return True


class Localizer(EaselTool, configurator.Configurable):
    """
    Easel tool, used for localization of the new point for drawing.
    Displays straight lines, first one moving in vertical and the second one in
    horizontal direction.
    """
    __gtype_name__ = "PisakPaintLocalizer"
    __gsignals__ = {
        "point-declared": (
            GObject.SIGNAL_RUN_FIRST,
            None, (GObject.TYPE_FLOAT, GObject.TYPE_FLOAT,)),
        "horizontal-idle": (
            GObject.SIGNAL_RUN_FIRST,
            None, ()),
        "vertical-idle": (
            GObject.SIGNAL_RUN_FIRST,
            None, ())
    }

    def __init__(self):
        super().__init__()
        self.horizontal_timer = None
        self.vertical_timer = None
        self.max_cycles = -1
        self.line_color = Clutter.Color.new(0, 0, 0, 255)
        self.line_width = 5
        self.step_duration = 10
        self.step = 1
        self.apply_props()

    def run(self):
        """
        Turn on the localizer, declare initial parameters, begin the
        vertical line movement.
        """
        self.localized_x = None
        self.localized_y = None
        self.x = 0
        self.y = 0
        self.from_x = 0
        self.from_y = 0
        self.to_x = 0
        self.to_y = 0
        self.width, self.height = self.get_size()
        self.canvas.set_size(self.width, self.height)
        self.canvas.connect("draw", self._draw)
        self._run_vertical()

    def kill(self):
        """
        Stop all the on-going activities and kill the localizer.
        """
        if self.vertical_timer is not None \
           and self.vertical_timer.is_playing():
            self._clean_up_vertical()
            self.vertical_timer.stop()
        if self.horizontal_timer is not None and \
                self.horizontal_timer.is_playing():
            self._clean_up_horizontal()
            self.horizontal_timer.stop()

    def _run_vertical(self):
        self.vertical_timer = Clutter.Timeline.new(self.step_duration)
        repeat_count = self.max_cycles if self.max_cycles == -1 \
                 else self.max_cycles * self.width / self.step
        self.vertical_timer.set_repeat_count(repeat_count)
        self.vertical_timer.connect("completed", self._update_vertical)
        self.vertical_timer.connect("stopped", self._on_vertical_idle)
        self.click_handlers = [self._stop_vertical, self._run_horizontal]
        self.vertical_timer.start()

    def _update_vertical(self, event):
        self.x = self.from_x = self.to_x = (self.from_x + self.step) \
                 % self.width
        self.from_y, self.to_y = 0, self.height
        self.canvas.invalidate()

    def _on_vertical_idle(self, source, event):
        self._clean_up_vertical()
        self.emit("vertical-idle")

    def _stop_vertical(self, source, event):
        self._clean_up_vertical()
        self.vertical_timer.stop()
        self.localized_x = self.x

    def _clean_up_vertical(self):
        self.vertical_timer.disconnect_by_func(self._on_vertical_idle)
        self.vertical_timer.disconnect_by_func(self._update_vertical)

    def _run_horizontal(self, source, event):
        self.horizontal_timer = Clutter.Timeline.new(self.step_duration)
        repeat_count = self.max_cycles if self.max_cycles == -1 \
                 else self.max_cycles * self.width / self.step
        self.horizontal_timer.set_repeat_count(repeat_count)
        self.horizontal_timer.connect("completed", self._update_horizontal)
        self.horizontal_timer.connect("stopped", self._on_horizontal_idle)
        self.click_handlers = [self._stop_horizontal]
        self.horizontal_timer.start()

    def _update_horizontal(self, event):
        self.from_x, self.to_x = 0, self.width
        self.y = self.from_y = self.to_y = (self.y + self.step) % self.height
        self.canvas.invalidate()

    def _stop_horizontal(self, source, event):
        self._clean_up_horizontal()
        self.horizontal_timer.stop()
        self.localized_y = self.y
        self._point_declared()

    def _on_horizontal_idle(self, source, event):
        self._clean_up_horizontal()
        self.emit("horizontal-idle")

    def _clean_up_horizontal(self):
        self._clear_canvas()
        self.horizontal_timer.disconnect_by_func(self._on_horizontal_idle)
        self.horizontal_timer.disconnect_by_func(self._update_horizontal)
        self.canvas.disconnect_by_func(self._draw)

    def _point_declared(self, *args):
        self.emit("point-declared", self.localized_x, self.localized_y)

    def _draw(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        ctxt.set_line_width(self.line_width)
        ctxt.set_source_rgba(*self.line_rgba)
        if self.localized_x is not None:
            ctxt.move_to(self.localized_x, 0)
            ctxt.line_to(self.localized_x, self.height)
            ctxt.stroke()
        ctxt.move_to(self.from_x, self.from_y)
        ctxt.line_to(self.to_x, self.to_y)
        ctxt.stroke()
        return True


class Bender(EaselTool, configurator.Configurable):
    """
    Easel tool, displays line spanned between two declared points,
    with different levels of curvature.
    """
    __gtype_name__ = "PisakPaintBender"
    __gsignals__ = {
        "bend-point-declared": (
            GObject.SIGNAL_RUN_FIRST,
            None, (GObject.TYPE_FLOAT, GObject.TYPE_FLOAT)),
        "idle": (
            GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()
        self.max_cycles = -1
        self.step_duration = 50
        self.step = 10
        self.click_handlers = [self._on_user_decision]
        self.cycle_index = 0  # number of current bender cycle
        self.apply_props()

    def run(self, from_x, from_y, to_x, to_y, angle, color, line_width):
        """
        Turn on the bender, declare initial parameters, begin the
        bending animation.
        :param from_x: x coordinate of the line first point
        :param from_y: y coordinate of the line first point
        :param to_x: x coordinate of the line second point
        :param to_y: y coordinate of the line second point
        :param angle: angle of the line's plane in user's space in radians
        :param color: color of the bender line
        :param line_width: width of the bender line
        """
        self.width, self.height = self.get_size()
        self.canvas.set_size(self.width, self.height)
        self.angle = angle + math.pi/2
        self.canvas.connect("draw", self._draw)
        self.line_rgba = color
        self.from_x = from_x
        self.from_y = from_y
        self.to_x = to_x
        self.to_y = to_y
        self.middle_x = self.through_x = self.from_x + \
                        (self.to_x - self.from_x) / 2
        self.middle_y = self.through_y = self.from_y + \
                        (self.to_y - self.from_y) / 2
        self.step_x = math.cos(self.angle) * self.step
        self.step_y = math.sin(self.angle) * self.step
        self.line_width = line_width
        self.timer = Clutter.Timeline.new(self.step_duration)
        self.timer.set_repeat_count(-1)
        self.timer.connect("completed", self._update_bender)
        self.timer.connect("stopped", self._on_user_idle)
        self._update_bender(None)
        self.timer.start()

    def kill(self):
        """
        Stop all the on-going activities and kill the bender.
        """
        self._clean_up()
        self.timer.stop()

    def _on_user_decision(self, source, event):
        self._clean_up()
        self.timer.stop()
        self.emit("bend-point-declared", self.through_x, self.through_y)

    def _on_user_idle(self, source, event):
        self._clean_up()
        self.emit("idle")

    def _clean_up(self):
        self.timer.disconnect_by_func(self._update_bender)
        self.timer.disconnect_by_func(self._on_user_idle)
        self._clear_canvas()
        self.canvas.disconnect_by_func(self._draw)

    def _update_bender(self, event):
        through_x = self.through_x + self.step_x
        through_y = self.through_y + self.step_y
        if (through_x > self.width or through_x < 0
            or through_y > self.height or through_y < 0):
            self.step_x *= -1
            self.step_y *= -1
        self.through_x += self.step_x
        self.through_y += self.step_y
        self.canvas.invalidate()
        self._check_cycle_count()

    def _check_cycle_count(self):
        if math.ceil(self.through_x) == math.floor(self.middle_x):
            self.cycle_index += 1
            if self.cycle_index / 2 == self.max_cycles:
                self.timer.stop()
                self.cycle_index = 0

    def _draw(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        ctxt.set_line_cap(cairo.LINE_CAP_ROUND)
        ctxt.set_line_width(self.line_width)
        ctxt.move_to(self.from_x, self.from_y)
        ctxt.curve_to(self.from_x, self.from_y, self.through_x,
                      self.through_y, self.to_x, self.to_y)
        ctxt.set_source_rgba(*self.line_rgba)
        ctxt.stroke()
        return True


class Yardstick(EaselTool, configurator.Configurable):
    """
    Easel tool, widget displaying straigh line of increasing length, reflecting
    user's need for specifing line length.
    """
    __gtype_name__ = "PisakPaintYardstick"
    __gsignals__ = {
        "destination-declared": (
            GObject.SIGNAL_RUN_FIRST,
            None, (GObject.TYPE_FLOAT, GObject.TYPE_FLOAT)),
        "idle": (
            GObject.SIGNAL_RUN_FIRST,
            None, ()),
    }

    def __init__(self):
        super().__init__()
        self.step_duration = 100
        self.step = 10
        self.click_handlers = [self._on_user_decision]
        self.apply_props()

    def run(self, from_x, from_y, angle, color, line_width):
        """
        Turn on the yardstick, declare initial parameters, begin the
        measuring animation.
        :param from_x: x coordinate of the line base point
        :param from_y: y coordinate of the line base point
        :param angle: angle of the line's plane in user's space in radians
        :param color: color of the yardstick line
        :param line_width: width of the yardstick line
        """
        self.to_x = self.base_x = self.from_x = from_x
        self.to_y = self.base_y = self.from_y = from_y
        self.angle = angle
        self.line_rgba = color
        self.step_x = math.cos(self.angle) * self.step
        self.step_y = math.sin(self.angle) * self.step
        self.line_width = line_width
        self.width, self.height = self.get_size()
        self.canvas.set_size(self.width, self.height)
        self.canvas.connect("draw", self._draw)
        self.timer = Clutter.Timeline.new(self.step_duration)
        self.timer.set_repeat_count(-1)
        self.timer.connect("stopped", self._on_user_idle)
        self.timer.connect("completed", self._update_yardstick)
        self.timer.start()

    def kill(self):
        """
        Stop all the on-going activities and kill the yardstick.
        """
        self._clean_up()
        self.timer.stop()

    def _on_user_idle(self, source, event):
        self._clean_up()
        self.emit("idle")

    def _on_user_decision(self, source, event):
        self._clean_up()
        self.timer.stop()
        self.emit("destination-declared", self.to_x, self.to_y)

    def _clean_up(self):
        self.timer.disconnect_by_func(self._on_user_idle)
        self.timer.disconnect_by_func(self._update_yardstick)
        self._clear_canvas()
        self.canvas.disconnect_by_func(self._draw)

    def _on_screen_border(self):
        self._on_user_decision(None, None)

    def _update_yardstick(self, event):
        to_x = self.to_x + self.step_x
        to_y = self.to_y + self.step_y
        if 0 <= to_x <= self.width and 0 <= to_y <= self.height:
            self.to_x, self.to_y = to_x, to_y
            self.canvas.invalidate()
        else:
            self._on_screen_border()

    def _draw(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        ctxt.set_line_cap(cairo.LINE_CAP_ROUND)
        ctxt.set_line_width(self.line_width)
        ctxt.move_to(self.base_x, self.base_y)
        ctxt.line_to(self.to_x, self.to_y)
        ctxt.set_source_rgba(*self.line_rgba)
        ctxt.stroke()
        return True


class Easel(layout.Bin, configurator.Configurable):
    """
    Paint main widget, displaying canvas on which all the drawing is going on.
    Displays all the tools needed for proper drawing.
    Communicates with its own stage, connects signals.
    """
    __gtype_name__ = "PisakPaintEasel"
    __gsignals__ = {
        "exit": (
            GObject.SIGNAL_RUN_FIRST,
            None, ())
    }
    __gproperties__ = {
        "navigator": (
            Navigator.__gtype__,
            "navigator",
            "navigator instance",
            GObject.PARAM_READWRITE),
        "localizer": (
            Localizer.__gtype__,
            "localizer",
            "localizer instance",
            GObject.PARAM_READWRITE),
        "bender": (
            Bender.__gtype__,
            "bender",
            "bender instance",
            GObject.PARAM_READWRITE),
        "yardstick": (
            Yardstick.__gtype__,
            "yardstick",
            "yardstick instance",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        self.canvas = Clutter.Canvas()
        self.set_content(self.canvas)
        self.canvas_handler_id = self.canvas.connect("draw", self._draw)
        self.save_path = None  # where the current painting should be saved
        self.localizer = None
        self.navigator = None
        self.yardstick = None
        self.bender = None
        self.tools = []
        self.stage = None
        self.working_tool = None  # currently working tool
        self.stage_handler_id = None  # id of the current stage handler
        self.line_width = 10  # width of the drawing line
        self.line_rgba = (0, 0, 0, 1)  # current drawing color
        self.from_x = 0  # x coordinate of current spot
        self.from_y = 0  # x coordinate of current spot
        self.to_x = 0  # x coordinate of current destination spot
        self.to_y = 0  # y coordinate of current destination spot
        self.through_x = 0  # x coordinate of current through spot
        self.through_y = 0  # y coordinate of current through spot
        self.path_history = []  # history of drawing
        self.line_cap = cairo.LINE_CAP_ROUND  # cap of the draw lines
        self.angle = 0  # angle of the draw line direction
        self.connect("notify::mapped", self._on_mapped)
        self.connect("notify::size", self._on_size_changed)
        self.apply_props()

    @property
    def localizer(self):
        return self._localizer

    @localizer.setter
    def localizer(self, value):
        self._localizer = value
        if value is not None:
            self.tools.append(value)
            value.connect("point-declared", self._exit_localizer)
            value.connect("horizontal-idle", self._exit)

    @property
    def navigator(self):
        return self._navigator

    @navigator.setter
    def navigator(self, value):
        self._navigator = value
        if value is not None:
            self.tools.append(value)
            value.connect("angle-declared", self._exit_navigator)
            value.connect("idle", self._exit)

    @property
    def bender(self):
        return self._bender

    @bender.setter
    def bender(self, value):
        self._bender = value
        if value is not None:
            self.tools.append(value)
            value.connect("bend-point-declared", self._exit_bender)
            value.connect("idle", self._exit)

    @property
    def yardstick(self):
        return self._yardstick

    @yardstick.setter
    def yardstick(self, value):
        self._yardstick = value
        if value is not None:
            self.tools.append(value)
            value.connect("destination-declared", self._exit_yardstick)
            value.connect("idle", self._exit)

    def _on_size_changed(self, source, event):
        self.width, self.height = self.get_allocation_box().get_size()
        if self.width > 0 and self.height > 0:
            self._allocate_tools()
            self.canvas.handler_disconnect(self.canvas_handler_id)
            self.canvas.set_size(self.width, self.height)
            self.canvas_handler_id = self.canvas.connect("draw", self._draw)

    def _on_mapped(self, source, event):
        self.disconnect_by_func(self._on_mapped)
        if self.stage is None:
            self.stage = self.get_stage()
            self.background_rgba = utils.convert_color(
                self.get_background_color())
            self.clear_canvas()

    def _allocate_tools(self):
        for tool in self.tools:
            tool.set_size(self.width, self.height)
            if not self.contains(tool):
                self.add_child(tool)

    def _exit_localizer(self, source, from_x, from_y):
        self._hung_up_tools()
        self.from_x = from_x
        self.from_y = from_y
        self.run_navigator()

    def _exit_navigator(self, source, angle):
        self._hung_up_tools()
        self.angle = angle
        self.run_yardstick()

    def _exit_yardstick(self, event, to_x, to_y):
        self._hung_up_tools()
        self.to_x = to_x
        self.to_y = to_y
        self.run_bender()

    def _exit_bender(self, event, through_x, through_y):
        self._hung_up_tools()
        self.through_x = through_x
        self.through_y = through_y
        self.run_drawing()

    def _hung_up_tools(self):
        self.working_tool = None
        self.stage.handler_disconnect(self.stage_handler_id)

    def _introduce_tool(self, tool):
        for item in self.tools:
            if item is not tool:
                item.hide()
        signal = pisak.app.window.input_group.action_signal
        self.stage_handler_id = self.stage.connect(signal, tool.on_user_click)
        self.working_tool = tool
        self.set_child_above_sibling(tool, None)
        tool.show()

    def _execute_on_canvas(self, drawing_method):
        self.canvas.handler_disconnect(self.canvas_handler_id)
        self.canvas_handler_id = self.canvas.connect("draw", drawing_method)
        self.canvas.invalidate()
        self.canvas.handler_disconnect(self.canvas_handler_id)
        self.canvas_handler_id = self.canvas.connect("draw", self._draw)

    def _draw_clear(self, cnvs, ctxt, width, height):
        ctxt.set_operator(cairo.OPERATOR_SOURCE)
        ctxt.set_source_rgba(*self.background_rgba)
        ctxt.paint()

    def _draw_to_file(self, cnvs, ctxt, width, height):
        if self.save_path:
            ctxt.get_target().write_to_png(self.save_path)
        return True

    def _draw_erase(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        if len(self.path_history) > 0:
            self.path_history.pop()
            for desc in self.path_history:
                ctxt.append_path(desc["path"])
                ctxt.set_line_width(desc["line_width"]+1)
                ctxt.set_line_cap(desc["line_cap"])
                ctxt.set_source_rgba(*desc["line_rgba"])
                ctxt.stroke()
        return True

    def _draw(self, cnvs, ctxt, width, height):
        self._draw_clear(cnvs, ctxt, width, height)
        for desc in self.path_history:
            ctxt.append_path(desc["path"])
            ctxt.set_line_width(desc["line_width"])
            ctxt.set_line_cap(desc["line_cap"])
            ctxt.set_source_rgba(*desc["line_rgba"])
            ctxt.stroke()
        ctxt.curve_to(self.from_x, self.from_y, self.through_x,
                      self.through_y, self.to_x, self.to_y)
        ctxt.set_line_width(self.line_width)
        ctxt.set_line_cap(self.line_cap)
        ctxt.set_source_rgba(*self.line_rgba)
        self.path_history.append({"path": ctxt.copy_path(),
                                  "line_width": self.line_width,
                                  "line_cap": self.line_cap,
                                  "line_rgba": self.line_rgba})
        ctxt.stroke()
        return True

    def _exit(self, event=None):
        self.clean_up()
        self.emit("exit")

    def run(self):
        """
        Run the initial easel tool.
        """
        self.run_localizer()

    def run_localizer(self):
        """
        Run the localizer tool, connect proper handler to the stage, connect
        signal to the localizer.
        """
        if self.working_tool is None:
            self._introduce_tool(self.localizer)
            self.localizer.run()

    def run_navigator(self):
        """
        Run the navigator tool, connect proper handler to the stage, connect
        signal to the navigator.
        """
        if self.working_tool is None:
            self._introduce_tool(self.navigator)
            self.navigator.run(self.from_x, self.from_y)

    def run_yardstick(self):
        """
        Run the yardstick tool, connect proper handler to the stage, connect
        signal to the yardstick.
        """
        if self.working_tool is None:
            self._introduce_tool(self.yardstick)
            self.yardstick.run(self.from_x, self.from_y, self.angle,
                               self.line_rgba, self.line_width)

    def run_bender(self):
        """
        Run the bender tool, connect proper handler to the stage, connect
        signal to the bender.
        """
        if self.working_tool is None:
            self._introduce_tool(self.bender)
            self.bender.run(self.from_x, self.from_y, self.to_x, self.to_y,
                            self.angle, self.line_rgba, self.line_width)

    def run_drawing(self):
        """
        Run drawing with previously declared parameters.
        """
        for tool in self.tools:
            tool.hide()
        self.canvas.invalidate()
        for tool in self.tools:
            tool.show()
        self.from_x, self.from_y = self.to_x, self.to_y
        self._exit()

    def clear_canvas(self):
        """
        Clear all the canvas, paint background.
        """
        self._execute_on_canvas(self._draw_clear)
        self.path_history = []

    def erase(self):
        """
        Erase the last drawn element.
        """
        self._execute_on_canvas(self._draw_erase)

    def _assign_file_name(self, idx):
        return os.path.join(SAVE_DIR, SAVE_FILE_BASENAME) + str(idx) + ".png"

    def save_to_file(self):
        """
        Save the canvas' current target to file in png format.
        """
        files_limit = 1000
        idx = 1
        file_name = self._assign_file_name(idx)
        while os.path.isfile(file_name) and idx <= files_limit:
            file_name = self._assign_file_name(idx)
            idx += 1
        self.save_path = file_name
        self._execute_on_canvas(self._draw_to_file)

    def clean_up(self, source=None):
        """
        Stop all the on-going activities, disconnect signals from the stage.
        """
        if self.working_tool is not None:
            self.working_tool.kill()
            self._hung_up_tools()
