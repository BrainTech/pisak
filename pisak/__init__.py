import os

from pisak.hooks import init_hooks
from pisak.unit import initialize as init_units
from pisak import settings

"""
Absolute path to the package directory.
"""
PATH = os.path.abspath(os.path.split(__file__)[0])

version = '1.0'


"""
Global configuration object that contains all the default settings.
"""
config = settings.Config()


"""
Instance of the current application.
"""
app = None


def init():
    init_hooks()
    init_units()
