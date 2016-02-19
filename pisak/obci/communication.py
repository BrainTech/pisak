

import subprocess
from functools import wraps


from pisak import logger
from pisak.obci import ws_client


LOG = logger.get_logger(__name__)

def run_cmd(cmd):
    try:
        p = subprocess.Popen(cmd.split())
        p.wait()
    except Exception as exc:
        LOG.error(exc)


def handle_obci_communication(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        run_cmd('obci kill_scenario pisak')
        run_cmd('obci launch pisak --ovr {}:{}'.format(
                ws_client.SERVER_HOST, ws_client.SERVER_PORT))

        # przekazać window

        window.

        def work(on_success, on_success_view_name, on_fail, fail_msg):
            obci_ws_client = ws_client.Client()
            start = time.time()
            while True:
                try:
                    obci_ws_client.connect()
                except (ConnectionRefusedError, WebSocketException) as exc:
                    LOG.error(exc)
                    if time.time() - start > 60:
                        Clutter.threads_add_idle(0, lambda *_: on_fail(
                            fail_msg, unwind='main_panel'))
                        return
                    else:
                        time.sleep(5)
                else:
                    break

            Clutter.threads_add_idle(
                0, lambda *_: on_success(success_view_name,
                                         {'ws_client': obci_ws_client,
                                          "init": False}))

        thread = threading.Thread(target=work, daemon=None,
                                  args=(window.load_view, window.load_popup))
        thread.start()


        ret = func(*args, **kwargs)
        run_cmd('obci kill_scenario pisak')
        return ret
    return wrapper



def get_ws_client():

    def work(on_success, on_fail):
        obci_ws_client = ws_client.Client()
        start = time.time()
        while True:
            try:
                obci_ws_client.connect()
            except (ConnectionRefusedError, WebSocketException) as exc:
                LOG.error(exc)

                if time.time() - start > 60:
                    Clutter.threads_add_idle(0, lambda *_: on_fail('Nie udało się połączyć z OBCI',
                                                                   unwind='main_panel'))
                    return
                else:
                    time.sleep(5)
            else:
                break

        global init
        init = False
        Clutter.threads_add_idle(
            0, lambda *_: on_success('obci/main',
                                     {'ws_client': obci_ws_client, "init": False}))

    thread = threading.Thread(target=work, daemon=None,
                              args=(window.load_view, window.load_popup))
    thread.start()