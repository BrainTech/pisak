if __name__ == '__main__':
    import random
    import time
    import asyncio
    import threading

    from ws4py.async_websocket import WebSocket
    from ws4py.server.tulipserver import WebSocketProtocol

    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = '28394'

    DUMMY_SEND = 'message from ws server'

    class DummyServer:

        clients = set()

        class DummyServerWebSocket(WebSocket):

            def __init__(self, *args, **kwargs):
                WebSocket.__init__(self, *args, **kwargs)

            def received_message(self, message):
                print(str(message))

            def opened(self):
                DummyServer.clients.add(self)

            def closed(self, _code, _reason=None):
                try:
                    DummyServer.clients.remove(self)
                except KeyError:
                    pass

        def __init__(self):
            self._server = None
            self._loop = asyncio.get_event_loop()
            self._worker = threading.Thread(
                target=self._start_server, daemon=True)

        def _create_server(self):
            return self._loop.create_server(
                lambda: WebSocketProtocol(
                    DummyServer.DummyServerWebSocket),
                SERVER_HOST,
                SERVER_PORT
            )

        def _start_server(self):
            asyncio.set_event_loop(self._loop)
            self._server = self._loop.run_until_complete(
                self._create_server())
            self._loop.call_soon(self._schedule_dummy_send)
            self._loop.run_forever()

        def _schedule_dummy_send(self):
            for client in self.clients:
                client.send(DUMMY_SEND)
            self._loop.call_later(random.randint(5, 10),
                                  self._schedule_dummy_send)

        def run(self):
            self._worker.start()

        def stop(self):
            self._server.close()
            self._server.wait_closed()
            self._loop.stop()
            self._worker.join()

    server = DummyServer()
    server.run()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        server.stop()