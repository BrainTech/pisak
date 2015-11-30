"""
Package designates a directory for resources.
"""
import os.path

"""
Absolute path to the package directory.
"""
PATH = os.path.abspath(os.path.split(__file__)[0])


def get(relative):
    """
    Get absolute resource path from relative resource.
    """
    return os.path.join(PATH, relative)
