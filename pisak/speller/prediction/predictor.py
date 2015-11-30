#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Prediction module. Uses Pressagio as an engine.
"""
import platform

import pressagio.callback
import pressagio

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from pisak import res


_DB_PATH = res.get("n_grams.sqlite")

_CONFIG_FILE = res.get("configs/predictor.ini")

_CONFIG_PARSER = configparser.ConfigParser()

_CONFIG_PARSER.read(_CONFIG_FILE)

_CONFIG_PARSER["Database"]["database"] = _DB_PATH


def get_predictions(string):
    """
    Get prediction for the given string.

    :param string: some string.

    :return: list of predictions, as strings.
    """
    callback = __CallbackClass(string)
    predictions = pressagio.Pressagio(callback, _CONFIG_PARSER).predict()
    if string.rstrip().split()[-1][0].isupper() and string[-1] != ' ':  # capital letters are handled here
        predictions = [p[0].upper() + p[1:] for p in predictions]
    if string in predictions:
        predictions.remove(string)
    return predictions


class __CallbackClass(pressagio.callback.Callback):
    def __init__(self, buffer):
        super().__init__()
        if platform.linux_distribution()[0] == 'Ubuntu':  # temporary fix
            self.buffer = ' ' + buffer
        else:	
            self.buffer = buffer

    def past_stream(self):
        return self.buffer

    def future_stream(self):
        return ''