"""
Blog application specific exceptions.
"""
from pisak import exceptions


class BlogInternetError(exceptions.PisakException):
    """
    Error raised when any problems with connecting to the Internet occur.
    """
    pass


class BlogAuthenticationError(exceptions.PisakException):
    """
    Error raised when an authentication attempt fails.
    """
    pass


class BlogMethodError(exceptions.PisakException):
    """
    Error raised when any unexpected blog-related condition occurs.
    """
    pass
