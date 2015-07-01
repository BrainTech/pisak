"""
Module defines generic PISAK exception.
"""
import traceback

from pisak import logger


_LOG = logger.get_logger(__name__)


class PisakException(Exception):
    """
    Base class for all other PISAK exceptions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log()

    def log(self):
        """
        Log information about the exception.
        """
        exc_msg = ''.join(traceback.format_exception(
            type(self), self, self.__traceback__))
        _LOG.info(exc_msg)


class NoInternetError(PisakException):
    """
    Exception thrown when an attempt to connect to the Internet fails.
    """
    pass
