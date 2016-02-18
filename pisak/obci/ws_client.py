import json

from ws4py.client.threadedclient import WebSocketClient
from ws4py.exc import WebSocketException

from pisak import logger


_LOG = logger.get_logger(__name__)


SERVER_HOST = '127.0.0.1'
SERVER_PORT = '28394'


class Client(WebSocketClient):

    SERVER_ADDRESS = 'ws://{}/ws'.format(
        ":".join([SERVER_HOST, SERVER_PORT]))

    def __init__(self):
        super().__init__(self.SERVER_ADDRESS)
        self.on_new_msg = None

    def received_message(self, msg):
        if callable(self.on_new_msg):
            self.on_new_msg(msg)

    def send_message(self, msg_type, msg_data=None):
        content = {'type': msg_type}
        if msg_data is not None:
            content.update({'data': msg_data})
        try:
            self.send(json.dumps(content))
        except WebSocketException as exc:
            _LOG.error(exc)