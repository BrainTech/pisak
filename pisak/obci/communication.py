import time
import threading
import subprocess
from functools import wraps

from gi.repository import Clutter
from ws4py.exc import WebSocketException

from pisak import logger
from pisak.obci import ws_client


_LOG = logger.get_logger(__name__)


OBCI_SCENARIO = 'pisak'


def handle_obci_scenario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        def run_cmd(cmd):
            try:
                p = subprocess.Popen(cmd.split())
                p.wait()
            except Exception as exc:
                _LOG.error(exc)

        run_cmd('obci kill_scenario {}'.format(OBCI_SCENARIO))
        run_cmd('obci launch {} --ovr {}:{}'.format(
                OBCI_SCENARIO, ws_client.SERVER_HOST, ws_client.SERVER_PORT))

        ret = func(*args, **kwargs)

        run_cmd('obci kill_scenario {}'.format(OBCI_SCENARIO))
        return ret
    return wrapper


def create_ws_client(window, on_success_view_name):
    window.load_popup('Trwa ładowanie...', icon=False)

    def work():
        obci_ws_client = ws_client.Client()
        start = time.time()
        while True:
            try:
                obci_ws_client.connect()
            except (ConnectionRefusedError, WebSocketException) as exc:
                _LOG.error(exc)
                if time.time() - start > 60:
                    Clutter.threads_add_idle(0, lambda *_: window.load_popup(
                        'Nie udało się połączyć z OBCI', unwind='main_panel'))
                    return
                else:
                    time.sleep(5)
            else:
                break

        Clutter.threads_add_idle(
            0, lambda *_: window.load_view(
                on_success_view_name, {'ws_client': obci_ws_client,
                                       "init": False}))

    thread = threading.Thread(target=work, daemon=None)
    thread.start()
