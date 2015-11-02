"""
Definitions of classes built-in with layout managers . These actors can
be used to describe whole application view in ClutterScript. Relevant
layout parameters are proxied to internal layout manager.
"""
from gi.repository import Clutter, GObject, Mx

from pisak import res, logger, unit, properties, configurator


_LOG = logger.get_logger(__name__)


class Box(Clutter.Actor, properties.PropertyAdapter, configurator.Configurable):
    """
    Arranges children in single line using BoxLayout.
    """
    __gtype_name__ = "PisakBoxLayout"

    __gproperties__ = {
        "orientation": (
            Clutter.Orientation.__gtype__,
            "", "",
            "horizontal",
            GObject.PARAM_READWRITE),
        "homogeneous": (
            GObject.TYPE_BOOLEAN,
            "whether children should be homo",
            "children homogeneous", False,
            GObject.PARAM_READWRITE),
        "spacing": (
            GObject.TYPE_UINT,
            "", "",
            0, GObject.G_MAXUINT, 0,
            GObject.PARAM_READWRITE),
        "ratio_width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio_height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio_spacing": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_bottom": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_top": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_right": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_left": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
    }

    def __init__(self):
        super().__init__()
        self.layout = Clutter.BoxLayout()
        self.set_layout_manager(self.layout)
        self.apply_props()


    def _set_px_spacing(self, *args):
        if hasattr(self, "ratio_spacing"):
            if self.layout.get_orientation() == Clutter.Orientation.HORIZONTAL:
                px_spacing = unit.w(self.ratio_spacing)
            elif self.layout.get_orientation() == Clutter.Orientation.VERTICAL:
                px_spacing = unit.h(self.ratio_spacing)
            self.layout.set_spacing(px_spacing)

    @property
    def orientation(self):
        return self.layout.get_orientation()

    @orientation.setter
    def orientation(self, value):
        self.layout.set_orientation(value)
        self._set_px_spacing()

    @property
    def spacing(self):
        return self.layout.get_spacing()

    @spacing.setter
    def spacing(self, value):
        self.layout.set_spacing(value)

    @property
    def homogeneous(self):
        return self.layout.get_homogeneous()

    @homogeneous.setter
    def homogeneous(self, value):
        self.layout.set_homogeneous(value)

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
    def ratio_spacing(self):
        return self._ratio_spacing

    @ratio_spacing.setter
    def ratio_spacing(self, value):
        self._ratio_spacing = value
        self._set_px_spacing()

    @property
    def ratio_margin_bottom(self):
        return self._ratio_margin_bottom

    @ratio_margin_bottom.setter
    def ratio_margin_bottom(self, value):
        self._ratio_margin_bottom = value
        self.set_margin_bottom(unit.h(value))

    @property
    def ratio_margin_top(self):
        return self._ratio_margin_top

    @ratio_margin_top.setter
    def ratio_margin_top(self, value):
        self._ratio_margin_top = value
        self.set_margin_top(unit.h(value))

    @property
    def ratio_margin_right(self):
        return self._ratio_margin_right

    @ratio_margin_right.setter
    def ratio_margin_right(self, value):
        self._ratio_margin_right = value
        self.set_margin_right(unit.w(value))

    @property
    def ratio_margin_left(self):
        return self._ratio_margin_left

    @ratio_margin_left.setter
    def ratio_margin_left(self, value):
        self._ratio_margin_left = value
        self.set_margin_left(unit.w(value))


class Bin(Clutter.Actor, properties.PropertyAdapter, configurator.Configurable):
    """
    Places its children on top of each other (overlaying them
    along the 'z' axis).
    """
    __gtype_name__ = "PisakBinLayout"
    __gproperties__ = {
        "ratio_width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio_height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio_margin_bottom": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_top": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_right": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "ratio_margin_left": (
            GObject.TYPE_FLOAT,
            None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
    }

    def __init__(self):
        super().__init__()
        self.apply_props()
        self.layout = Clutter.BinLayout()
        self.set_layout_manager(self.layout)

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
    def ratio_margin_bottom(self):
        return self._ratio_margin_bottom

    @ratio_margin_bottom.setter
    def ratio_margin_bottom(self, value):
        self._ratio_margin_bottom = value
        self.set_margin_bottom(unit.h(value))

    @property
    def ratio_margin_top(self):
        return self._ratio_margin_top

    @ratio_margin_top.setter
    def ratio_margin_top(self, value):
        self._ratio_margin_top = value
        self.set_margin_top(unit.h(value))

    @property
    def ratio_margin_right(self):
        return self._ratio_margin_right

    @ratio_margin_right.setter
    def ratio_margin_right(self, value):
        self._ratio_margin_right = value
        self.set_margin_right(unit.w(value))

    @property
    def ratio_margin_left(self):
        return self._ratio_margin_left

    @ratio_margin_left.setter
    def ratio_margin_left(self, value):
        self._ratio_margin_left = value
        self.set_margin_left(unit.w(value))
