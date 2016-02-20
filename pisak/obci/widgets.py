import random

from gi.repository import Clutter, Mx, GObject

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

    def __init__(self):
        super().__init__()
        self._non_targets_left = 0
        self._previous_targets = 0
        self._face = None
        self._with_target = False
        self.connect("notify::size", lambda *_: self._rescale_face())

    def _rescale_face(self):
        if self._face is not None:
            self._face.set_size(*self.get_size())

    def _now_target(self):
        if self._previous_targets > 0:
            self._previous_targets -= 1
            if self._previous_targets == 0:
                self._non_targets_left = random.randint(0, 5)
            return False
        elif self._non_targets_left > 0:
            self._non_targets_left -= 1
            return False
        else:
            now_target = random.randint(0, 1)
            if now_target:
                self._previous_targets = 2
                return True
            else:
                return False

    @property
    def with_target(self):
        return self._with_target

    @with_target.setter
    def with_target(self, value):
        self._with_target = value
        if value and self._face is None:
            self._face = Mx.Image()
            self._face.set_from_file(self.FACE_PATH)
            self._face.set_scale_mode(Mx.ImageScaleMode.FIT)
            self._face.hide()
            self.get_parent().add_child(self._face)

    def enable_hilite(self):
        self.style_pseudo_class_add('hilited')
        if self._with_target and self._now_target():
            self._face.show()
            return True
        else:
            return False

    def disable_hilite(self):
        self.style_pseudo_class_remove('hilited')
        if self.with_target:
            self._face.hide()
