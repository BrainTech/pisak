"""
Various global hooks.
"""
import sys
import threading
import traceback

from . import logger


_LOG = logger.get_logger(__file__)


_MESSAGES = {
    "unexpected_error": "Wystąpił nieoczekiwany błąd.\n"
                        "Aplikacja zostanie zamknięta."
}


def _register_custom_excepthook():
    """
    Register custom function to be used as sys.excepthook for
    the current application. It will: handle any exception that
    has not been caught by the application
    itself; log the error as critical; if the application main loop is still
    alive then display some GUI message and then close the application,
    otherwise just do nothing and let the application close itself; only
    exceptions originating from the main thread are handled;
    call the default, built-in `sys.__excepthook__` function in the end.
    """
    def excepthook(exctype, value, traceb):
        import pisak
        if exctype in (KeyboardInterrupt, SystemExit):
            pass
        else:
            _LOG.critical(''.join(traceback.format_exception(
                exctype, value, traceb)))

            if (isinstance(threading.currentThread(),
                    threading.main_thread().__class__) and
                    pisak.app is not None and
                    pisak.app.main_loop_is_running):
                try:
                    pisak.app.window.load_popup(
                        _MESSAGES["unexpected_error"], pisak.app.main_quit)
                except Exception as exc:
                    _LOG.critical(exc)

        sys.__excepthook__(exctype, value, traceb)
    sys.excepthook = excepthook


def _register_thread_excepthook():
    """
    Monkey patch the `threading.Thread.run` method in order to catch
    all the uncaught exceptions that happened in a thread with
    an exception hook.
    """
    init_old = threading.Thread.__init__
    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run
        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except:
                sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init


def _register_custom_print_exception():
    """
    Monkey patch the `traceback.print_exception` function in order to log
    information about all the incoming exceptions, before printing them.
    """
    print_exception_old = traceback.print_exception
    def print_exception(exctype, value, traceb, limit=None, file=None, chain=True):
        _LOG.error(''.join(traceback.format_exception(
            exctype, value, traceb, limit, file, chain)))
        print_exception_old(exctype, value, traceb, limit, file, chain)
    traceback.print_exception = print_exception


def init_hooks():
    """
    Register all the hooks. Should be called as soon as a program starts.
    """
    _register_custom_excepthook()
    _register_thread_excepthook()
    _register_custom_print_exception()
