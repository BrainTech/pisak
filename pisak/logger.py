import os
import logging
from logging import handlers

from pisak import arg_parser

HOME = os.path.expanduser("~")
HOME_PISAK_DIR = os.path.join(HOME, ".pisak")
HOME_LOGS_DIR = os.path.join(HOME_PISAK_DIR, "logs")


LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LEVELS['debug'])

    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_formatter = logging.Formatter(console_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    file = 'pisak.log'
    path = os.path.expanduser('~/.pisak/logs/')
    if not os.path.exists(path):
        os.makedirs(path)
    file_format = '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
    file_formatter = logging.Formatter(file_format)

    file_handler = handlers.RotatingFileHandler(path + file,
                                                maxBytes=10**7,
                                                backupCount=10)
    if arg_parser.get_args().debug:
        file_handler.setLevel(LEVELS['debug'])
        console_handler.setLevel(LEVELS['debug'])
    else:
        file_handler.setLevel(LEVELS['warning'])
        console_handler.setLevel(LEVELS['error'])
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_event_logger():
    """
    Get logger devoted to some specific events that happened to the PISAK program.
    """
    logger = logging.getLogger("PISAK events")
    logger.setLevel(LEVELS['info'])
    console_format = '%(asctime)s - %(message)s'
    console_formatter = logging.Formatter(console_format)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    filename = "events.log"
    file = os.path.join(HOME_LOGS_DIR, filename)
    file_format = '%(asctime)s - %(message)s'
    file_formatter = logging.Formatter(file_format)
    file_handler = handlers.RotatingFileHandler(file,
                                                maxBytes=10**7,
                                                backupCount=10)
    file_handler.setLevel(LEVELS['info'])
    console_handler.setLevel(LEVELS['info'])
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


OBCI_LOGS_PATH = os.path.join(HOME_LOGS_DIR, 'obci_logs.txt')

class _OBCILogger:

    PATH = OBCI_LOGS_PATH

    def __init__(self):
        self._logs = []

    def log(self, time, event):
        """
        Log an event.

        :param time: time.time() of the event.
        :param event: name of the event.
        """
        self._logs.append(' '.join([str(time), event]) + '\n')

    def save(self):
        if self._logs:
            with open(self.PATH, 'a') as file:
                file.writelines(self._logs)
            self._logs.clear()


def get_obci_logger():
    """
    Get a logger suited for OBCI..
    """
    return _OBCILogger()