"""
Websocket server and client implementations for PISAK eyetrackers.
"""
import asyncio
import threading

from ws4py.async_websocket import WebSocket
from ws4py.server.tulipserver import WebSocketProtocol
from ws4py.client.threadedclient import WebSocketClient

from pisak import logger


_LOG = logger.get_logger('tracker')

SERVER_HOST = '127.0.0.1'
SERVER_PORT = '28394'

CLIENT_START_MSG = 'start'
CLIENT_STOP_MSG = 'stop'


class TrackerServer(object):
    """
    Server for trackers.
    """

    clients = set()

    class TrackerServerWebSocket(WebSocket):
        """
        Handler web socket class for new coming connections.
        """

        def __init__(self, *args, **kwargs):
            WebSocket.__init__(self, *args, **kwargs)
            self.active = False

        def received_message(self, message):
            """
            Implementation of the`WebSocket` method, called when a new message
             arrives.

            :param message: received message. Must be a
            `BinaryMessage`instance.
            """
            msg = str(message)
            if msg == CLIENT_START_MSG:
                self.active = True
            elif msg == CLIENT_STOP_MSG:
                self.active = False

        def opened(self):
            """
            Implementation of the`WebSocket` method, called when the connection
            is opened. Client is then added to the set of all clients.
            """
            _LOG.debug("New connection opened: {}".format(self))
            TrackerServer.clients.add(self)

        def closed(self, _code, _reason=None):
            """
            Implementation of the`WebSocket` method, called when the connection
            is closed, no matter by which side. Client is then removed from the set
            of all clients.

            :param _code: code of the connection. Unused argument passed
            by the `WebSocket` internally.
            :param _reason: reason of closing the connection. Unused
            argument passed by the `WebSocket` internally.
            """
            _LOG.debug("Connection to client closed: {}".format(self))
            try:
                TrackerServer.clients.remove(self)
            except KeyError:
                _LOG.warning("Client {} had not been registered.".format(self))

    def __init__(self, tracker):
        self._tracker = tracker
        self._server = None
        self._loop = asyncio.get_event_loop()
        self._worker = threading.Thread(target=self._start_server, daemon=True)

    def _create_server(self):
        """
        Create server based on the web sockets system.

        :return: server created.
        """
        return self._loop.create_server(
            lambda: WebSocketProtocol(
                TrackerServer.TrackerServerWebSocket),
            SERVER_HOST,
            SERVER_PORT
        )

    def _start_server(self):
        """
        Prepare and make the server serve within the asyncio event loop.
        """
        asyncio.set_event_loop(self._loop)
        self._server = self._loop.run_until_complete(self._create_server())
        self._loop.add_reader(self._tracker.stdout, self._read_from_tracker)
        self._loop.run_forever()

    def _read_from_tracker(self):
        """
        Read form the tracker standard output and send data to all the
        active clients.
        """
        data = self._tracker.stdout.readline()
        if not data:
            return
        data = data.decode('utf-8', 'ignore').strip()
        if 'gaze_pos:' in data:
            data_to_send = data.replace('gaze_pos:', '').strip()
            for client in self.clients:
                if client.active:
                    client.send(data_to_send)

    def run(self):
        """
        Run the server. Server is run in a separate thread.
        """
        self._worker.start()

    def stop(self):
        """
        Stop and close the server, close the server thread.
        """
        self._server.close()
        self._server.wait_closed()
        self._loop.stop()
        self._worker.join()


class TrackerClient(WebSocketClient):
    """
    Tracker server client.
    """

    SERVER_ADDRESS = 'ws://{}/ws'.format(
        ":".join([SERVER_HOST, SERVER_PORT]))

    def __init__(self, target):
        _LOG.debug('TrackerClient.__init__: {}, {}'.format(self.SERVER_ADDRESS, target))
        super().__init__(self.SERVER_ADDRESS)
        self.target = target  # target for data coming from the tracker server

    def activate(self):
        """
        Activate the client. Activated client will be able to receive data from
         the tracker server.
        """
        self.send(CLIENT_START_MSG)

    def deactivate(self):
        """
        Deactivate the client. Deactivated client will not be able to receive data from
         the tracker server but its connection will remain opened.
        """
        if not self.terminated:
            self.send(CLIENT_STOP_MSG)

    def received_message(self, data):
        """
        Implementation of the`WebSocketClient` method, called when a new
        data arrives.

        :param data: received binary data item.
        """
        self.target.on_new_data(str(data))

if __name__ == '__main__':
    import os
    import time
    import subprocess
    from pisak import dirs

    command = os.path.join(
        dirs.HOME,
        "pisak", "eyetracker", "mockup",
        "pisak-eyetracker-mockup"
    ) + ' --tracking'
    process = subprocess.Popen(command.split(), shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    device_server = TrackerServer(process)
    device_server.run()  # this method is non-blocking
    time.sleep(1.0)

    class ClientMockup:
        def on_new_data(self, data):
            print('on_new_data: {}'.format(data))

    client_mockup = ClientMockup()

    tracker_client = TrackerClient(client_mockup)
    tracker_client.connect()
    tracker_client.activate()

    while True:
        time.sleep(0.5)
