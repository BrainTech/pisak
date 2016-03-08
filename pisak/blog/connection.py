import queue
import threading

from gi.repository import Clutter


class ConnectionManager:

    def __init__(self):
        self._input_queue = queue.Queue()
        self._output_queue = queue.Queue()
        self._timeout = -1
        self._working = True

        self._th = threading.Thread(target=self._worker, daemon=True)
        self._th.start()

    def _worker(self):
        while self._working:
            request = self._input_queue.get()
            response = self.process_request(request)
            self._output_queue.put(response)

    def _do_make_request(self, request, on_response):
        self._input_queue.put(request, timeout=self._timeout)
        data = self._output_queue.get(timeout=self._timeout)
        Clutter.threads_add_idle(0, on_response, data)

    def make_request(self, on_response, api, method, *args, **kwargs):
        """
        Make a new request.

        :param on_response: callback called when the request will be processed
        return a response.
        :param api: api that the request should be made to.
        :param method: api method to be used.
        :param args: optional arguments passed with the method.
        :param kwargs: optional keyword arguments passed with the method.
        """
        request = (api, method, args, kwargs)
        th = threading.Thread(target=self._do_make_request,
                              args=(request, on_response), daemon=True)
        th.start()

    def process_request(self, request):
        """
        Process the given request in some specific way.

        :param request: tuple consisting of: api, method, args, kwargs.

        :return: data.
        """
        raise NotImplementedError


class BlogClientManager(ConnectionManager):

    def _get_current_blog(self, api):
        if api == 'wordpress':
            blog = None  # user's wordpress blog
        elif api == 'rest':
            blog = None  # some public blog
        return blog

    def process_request(self, request):
        """
        Send a request to the proper blog API and return a response.

        :param request: tuple consisting of: api, method, args, kwargs.

        :return: data.
        """
        api, method, args, kwargs = request
        client = self._get_current_blog(api)
        if hasattr(client, method):
            func = getattr(client, method)
            data = func(*args, **kwargs)
            return data