"""
Module for managing style-related issues.
"""
from gi.repository import Mx


class StylableContainer(object):
    """
    Base class for objects being containers of stylables that propagate
    their style class prop for descendants
    """
    def _recursive_apply_style(self, actor):
        if isinstance(actor, Mx.Stylable) and actor is not self:
            if isinstance(self, Mx.Stylable) and self.get_style_class():
                actor.set_style_class(self.get_style_class())
            elif hasattr(self, "style_class"):
                actor.set_style_class(self.style_class)
        for child in actor.get_children():
            self._recursive_apply_style(child)

    def _do_connect_container(self, actor):
        actor.connect("actor-added", lambda parent, descendant:
                        self._recursive_apply_style(self))
        actor.connect("actor-added", lambda parent, descendant:
                              self._recursive_connect_container(descendant))

    def _recursive_connect_container(self, actor):
        self._do_connect_container(actor)
        for item in actor.get_children():
            self._do_connect_container(item)
            self._recursive_connect_container(item)

    def _connect(self):
        self._recursive_connect_container(self)
        self.connect("notify::style-class",
                lambda actor, param: self._recursive_apply_style(actor))
        self.connect("notify::style-class", lambda *_: self.apply_props())

    def apply_props(self):
        raise NotImplementedError

    def prepare_style(self):
        """
        Prepare object and all its descendants to follow all
        the style requirements.
        """
        self._connect()
