import os

from pisak.hooks import init_hooks
from pisak import settings, css_parser, dirs

"""
Absolute path to the package directory.
"""
PATH = os.path.abspath(os.path.split(__file__)[0])

version = '1.0'


"""
Global configuration object that contains all the default settings.
"""
config = settings.Config()

""""
Global css object.
"""
css = css_parser.CssToDict(dirs.get_css_path())

"""
Instance of the current application.
"""
app = None


def init():
    """
    Should be run on the PISAK program start before doing anything else.
    Initializes any necessary tools, processes or resources.
    """
    init_hooks()
