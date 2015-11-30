"""
Implementation of signal connecting strategy for ClutterScript.
"""
import sys
import inspect
from functools import wraps

from gi.repository import GObject

from pisak import logger


_LOG = logger.get_logger(__name__)


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
    """
    Wrapper that connects a GObject signals handlers in a proper way,
    taking into consideration any requested flags or parameters.

    :param gobject: any :class:`GObject.GObject` instance.
    :param signal: signal name.
    :param target: object that should be passed to the handler as an argument,
    can be None.
    :param flags: any extra flags, supported now: GObject.ConnectFlags.AFTER.
    :param function: callable, handler function.
    :param data: any extra data, can be anything, depending
    on the 'function' signature.
    """
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


def connect_registered(script, gobject, signal, handler, target, flags, data):
    """
    Alternate implementation of signal connector. Uses only registered
    functions instead of introspection.

    :param script: ClutterScript.
    :param gobject: any :class:`GObject.GObject` instance.
    :param signal: signal name.
    :param handler: callable, handler function.
    :param target: object that should be passed to the handler as an argument,
    can be None.
    :param flags: any extra flags, supported now: GObject.ConnectFlags.AFTER.
    :param data: any extra data, can be anything, depending
    on the 'function' signature.
    """
    function = resolve_registered(handler)
    wrapped = wrap_function(function)
    connect_function(gobject, signal, target, flags, wrapped, data)


_HANDLER_MAP = {}

def resolve_registered(handler):
    """
    Resolve registered function.

    :param handler: handler name.

    :return: callable, previously registered function.
    """
    function = _HANDLER_MAP.get(handler)
    if function is not None:
        return function
    else:
        raise Exception("No such function: " + handler)


def register_function(handler, function):
    """
    Registers a function as handler.

    :param handler: handler name.
    :param function: callable, handler function.
    """
    if callable(function):
        _HANDLER_MAP[handler] = function
    else:
        raise Exception("Not a function", function)


def registered_handler(handler_name):
    """
    Decorator.

    :param handler_name: name that the function should be regitered with.
    """
    def f_reg(function):
        register_function(handler_name, function)
        return function
    return f_reg
