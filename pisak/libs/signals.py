'''
Implementation of signal connecting strategy for ClutterScript.
'''
import sys
import inspect
from functools import wraps

from gi.repository import GObject

from pisak import logger


_LOG = logger.get_logger(__name__)


"""
Object or module relative to which signal handlers are named
"""
BASE_NAMESPACE = sys.modules[__name__]


def resolve_name(handler_name):
    """
    Resolve python name to python value in current namespace
    """
    import pisak.handlers  # @UnusedImport
    name_parts = handler_name.split('.')
    current = BASE_NAMESPACE
    for part in name_parts:
        current = current.__dict__[part]
    return current


def resolve_handler(handler_name):
    """
    Resolve handler name and check for callability
    """
    function = resolve_name(handler_name)
    if callable(function):
        return function
    else:
        raise Exception("Specified handler is not a function")


def wrap_function(function):
    """
    Decorator that wraps a given function with some master function.

    :param function: function to be wrapped.

    :return: wrapper function with the given function wrapped inside.
    """
    @wraps(function)
    def master_wrapper(*master_args):
        """
        Master function which can accept any number of non-keyword
        arguments, inspects a wrapped function arguments specification
        and then just calls it in a proper way. If there are more arguments passed
        than the function can accept, then the excessive ones are ignored.
        """
        args, varargs, _keywords, _defaults = inspect.getargspec(function)
        if not varargs and len(master_args) > len(args):
            _LOG.warning("Excessive arguments: {}, for function: {}".format(
                master_args[len(args) : ], function))
            master_args = master_args[ : len(args)]
        return function(*master_args)
    return master_wrapper


def connect_function(gobject, signal, target, flags, function, data):
    # TODO:
    # make 'git grep connect' and redirect all the resulted connections in here
    if target is not None:
        if GObject.ConnectFlags.AFTER == flags:
            gobject.connect_object_after(signal, function, target, data)
        else:
            gobject.connect_object(signal, function, target, data)
    elif GObject.ConnectFlags.AFTER == flags:
        gobject.connect_after(signal, function, data)
    else:
        gobject.connect(signal, function, data)


def python_connect(script, gobject, signal, handler, target, flags, data):
    """
    Implementation of signal connector used by
    ClutterScript.connect_signals_full.
    """
    function = resolve_handler(handler)
    wrapped = wrap_function(function)
    connect_function(gobject, signal, target, flags, wrapped, data)


_HANDLER_MAP = {}

def resolve_registered(handler):
    """
    Resolve registered function
    """
    function = _HANDLER_MAP.get(handler)
    if function is not None:
        return function
    else:
        raise Exception("No such function: " + handler)


def register_function(handler, function):
    """
    Registers a function as handler
    """
    if callable(function):
        _HANDLER_MAP[handler] = function
    else:
        raise Exception("Not a function", function)


def registered_handler(handler_name):
    """
    Decorator
    """
    def f_reg(function):
        register_function(handler_name, function)
        return function
    return f_reg


def connect_registered(script, gobject, signal, handler, target, flags, data):
    """
    Alternate implementation of signal connector. Uses only registered
    functions instead of introspection.
    """
    function = resolve_registered(handler)
    wrapped = wrap_function(function)
    connect_function(gobject, signal, target, flags, wrapped, data)
