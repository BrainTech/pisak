"""
Management center of any PISAK settings. Declares one class that loads the main
configuration file and stores all the settings.
"""
import configobj

from pisak import logger, dirs


_LOG = logger.get_logger(__name__)


class Config(configobj.ConfigObj):
    """
    Default configuration object.
    """

    def __init__(self):
        super().__init__(encoding="UTF-8")
        self._load_defaults()

    def _load_defaults(self):
        defaults = dirs.get_general_configs()
        self.update_config(defaults)

    def update_config(self, config_paths):
        """
        Updates the already existing config with content of some another
        given config files. Overwrites all the common properties.

        :param config_paths: single path to a config file or list of paths
        """
        if isinstance(config_paths, str):
            config_paths = [config_paths]
        if isinstance(config_paths, list):
            for path in config_paths:
                try:
                    self.merge(configobj.ConfigObj(path, encoding='UTF8'))
                except configobj.ConfigObjError as error:
                    _LOG.warning(error)
        else:
            message = "{} is not permitted type for the config paths." \
                      "Config paths must be either a list or a single string".\
                    format(type(config_paths))
            _LOG.error(message)
            raise TypeError(message)
