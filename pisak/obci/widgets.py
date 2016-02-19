from gi.repository import Clutter, Mx

from pisak import widgets, properties, res


class CalibrationLabel(widgets.Label, properties.PropertyAdapter):

    __gtype_name__ = "PisakOBCICalibrationLabel"

    __gproperties__ = {
        "with_target": (
            GObject.TYPE_BOOLEAN,
            "", "", False,
            GObject.PARAM_READWRITE)
    }

    FACE_PATH = res.get('sample.jpg')

    HILITE_COLOR = Clutter.Color.new(220, 220, 220, 250)
    REST_COLOR = Clutter.Color.new(50, 50, 50, 250)

    def __init__(self):
        super.__init__()
        self._face = None
        self._with_target = False

    @property
    def with_target(self):
        return self._with_target

    @with_target.setter
    def with_target(self, value):
        self._with_target = value
        if value and self._face is None:
            self._face = Mx.Image()
            self._face.set_from_file(FACE_PATH)

    def enable_hilite(self, target=False):
        self.set_color(self.HILITE_COLOR)
        if target and self._with_target and self._face not in self.get_children():
            self.add_child(self._face)

    def disable_hilite(self):
        self.set_color(self.REST_COLOR)
        if self.with_target and self._face in self.get_children():
            self.remove_child(self._face)
