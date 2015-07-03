"""Module defines a single method get_logger that returns logger with
set logging level. Change loggin.INFO lines to change logging level."""
import logging
from logging import DEBUG, ERROR, INFO, WARNING, Logger
import sys
import time
LOGGING_LEVEL = logging.DEBUG
TRACEBACK_LEVEL = logging.CRITICAL
import math
class CustomLogger(Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None):
        try:
            super(CustomLogger, self)._log(level, msg, args, exc_info, extra)
        except ValueError:
            # Probably NaN in time.time()
            sys.stderr.write(str(time.time()) + ' ')
            sys.stderr.write(msg)
            sys.stderr.write('\n')
            if exc_info:
                import traceback
                traceback.print_exception(*exc_info)

logging.setLoggerClass(CustomLogger)
_loggers = set()
class MyFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%H:%M:%S", ct)
            if not math.isnan(record.msecs):
                s = "%s,%03d" % (s, int(record.msecs))
        return s

def get_logger(p_name):
    """Return logger with p_name as name."""
    l_logger = logging.getLogger(p_name)
    if len(l_logger.handlers) > 0:
        return l_logger
    _loggers.add(l_logger)
    l_handler = StdErrStreamHandler()

    l_logger.setLevel(LOGGING_LEVEL)
    l_handler.setLevel(LOGGING_LEVEL)

    l_formatter = MyFormatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
    l_handler.setFormatter(l_formatter)
    l_logger.addHandler(l_handler)
    return l_logger

def set_logging_level(level):
    global LOGGING_LEVEL
    LOGGING_LEVEL = level
    for logger in _loggers:
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

class StdErrStreamHandler(logging.StreamHandler):
    def set_stream(self, stream):
        pass
    def get_stream(self):
        import sys
        return sys.stderr
    stream = property(get_stream, set_stream)
