"""
Module contains one main class called Configurable. When inherited, it serves
as an utility for an object and enables to apply all the configuration
parameters taken from an configuration file.
Parameters appropriate for a given object are picked only if they are
assigned to a correct key. The key itself is determined according to the keys
hierarchy, for the first found, existing characteristic of the object:
first 'style-class' property is looked for, then GObject object type name
and finally pythonic object type name (class name).
"""
from gi.repository import Mx

import pisak
from pisak import logger


_LOG = logger.get_logger(__name__)


class Configurable(object):
    """
    Class initializing config for other PISAK classes.
    """

    def __init__(self):
        super().__init__()
        self._config_obj = None

    @property
    def config(self):
        """
        Current configuration object that
        contains all the specification.
        """
        return self._config_obj

    @config.setter
    def config(self, value):
        self._config_obj = value

    def apply_props(self, extra_configs=None):
        """
        Apply all the properties from the config.

        :param extra_configs: if any extra configs should be applied.
        List of many or single string are accepted.
        """
        self.config = pisak.config
        if extra_configs:
            self.config.update_config(extra_configs)
        if self.config is None:
            msg = "Config object has not been initialized. Properties can not be applied."
            _LOG.warning(msg)
            return
        if isinstance(self, Mx.Stylable) and self.get_style_class():
            name = self.get_style_class()
        elif hasattr(self, "style-class") and self.style_class is not None:
            name = self.style_class
        elif hasattr(self, "__gtype_name__") and self.__gtype_name__ is not None:
            name = self.__gtype_name__
        else:
            name = type(self).__name__
        if name in self.config.keys():
            for prop_name, prop_value in self.config[name].items():
                setattr(self, prop_name, prop_value)
