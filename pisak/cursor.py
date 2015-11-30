"""
Module handles cursor-style (stream of coordinates) input in JSON layout.
"""
import time

from gi.repository import GObject, Clutter

from pisak import logger, scanning, configurator, layout, unit, tracker

_LOG = logger.get_logger(__name__)


class Sprite(layout.Bin, configurator.Configurable):
    """
    Sprite (virtual cursor) object. It displays a big dot in a bright color
    on the screen which follows input coordinates and selects GUI controls
    on a timeouted hover.
    """

    __gtype_name__ = "PisakSprite"

    __gproperties__ = {
        "timeout": (
            GObject.TYPE_UINT,
            "", "",
            0, GObject.G_MAXUINT, 1600,
            GObject.PARAM_READWRITE)
    }
    
    def __init__(self):
        super().__init__()
        self._timeout = 1

        self.container = None
        self.clickables = None
        self._running = False
        self.hover_start = None
        self.hover_actor = None
        self.initial_position = (-10, -10)
        self.all_rescan = []
        self.coords = (0, 0)
        self.set_x_expand(True)
        self.set_y_expand(True)
        self._init_sprite()
        self.tracker_client = tracker.TrackerClient(self)
        self.tracker_client.connect()
        self.apply_props()

    def _init_sprite(self):
        self.sprite = Clutter.Actor()
        self.sprite.set_size(20, 20)
        self.sprite.set_background_color(Clutter.Color.new(255, 255, 0, 255))
        self.add_actor(self.sprite)
        self.update_sprite(self.initial_position)

    def _rescan(self, *source):
        self.clickables = None

    def _do_disconnect(self, obj, func):
        try:
            obj.disconnect_by_func(func)
        except TypeError as e:
            _LOG.warning(e)

    def _disconnect_rescan(self):
        self._do_disconnect(self.container, self._rescan)
        for obj in self.all_rescan:
            self._do_disconnect(obj, self._rescan)

    def _connect_rescan(self):
        self.all_rescan = []
        self.container.connect("allocation-changed", self._rescan)
        to_conn = self.container.get_children()
        while len(to_conn) > 0:
            current = to_conn.pop()
            current.connect("allocation-changed", self._rescan)
            self.all_rescan.append(current)
            to_conn = to_conn + current.get_children()

    @property
    def timeout(self):
        """
        Selection hover timeout, in miliseconds. Default is 1 second.
        """
        return self._timeout * 1000
    
    @timeout.setter
    def timeout(self, value):
        self._timeout = int(value) / 1000
    
    def parse_coords(self, data):
        """
        Parses raw data line into x-y coordinates tuple.

        :param data: raw data with coordinates, being a single-line
        string in a format: 'screenWidth% screenHeight%'.

        :return: tuple with cursor parsed x and y coordinates, in pixels as floats.
        """
        if not data:
            return self.coords
        try:
            coords = tuple(float(x) for x in data.split(' '))
            coords = (round(coords[0] * unit.size_pix.width), round(coords[1] * unit.size_pix.height))
            self.coords = coords
        except Exception as ex:
            raise Exception("Error parsing coordinates data: {}".format(ex))
        return self.coords

    def update_sprite(self, coords):
        """
        Changes cursor position on the screen.

        :param coords: tuple with x and y coordinates.
        """
        x, y = (coords[0] - self.sprite.get_width() / 2), (coords[1] - self.sprite.get_height() / 2)
        self.sprite.set_position(x, y)

    def scan_clickables(self):
        """
        Detects any widgets that could be possibly clicked
        and puts them on a list used by :func:`find_actor`.
        """
        if self.container is None:
            self.clickables = []
            return
        to_scan = self.container.get_children()
        clickables = []
        while len(to_scan) > 0:
            current = to_scan.pop()
            if isinstance(current, scanning.Scannable):
                if not current.is_disabled():
                    clickables.append(current)
            to_scan = to_scan + current.get_children()
        self.clickables = clickables
        _LOG.debug("clickables: {}".format(clickables))
    
    def find_actor(self, coords):
        """
        Looks for any widget positioned at a given coordinates.
        If a widget is found then it is returned, otherwise returns None.

        :param coords: tuple with x-y coordinates.

        :return: some found widget or None.
        """
        if self.clickables is None:
            self.scan_clickables()
        for clickable in self.clickables:
            (x, y), (w, h) = clickable.get_transformed_position(), clickable.get_size()
            if (x <= coords[0]) and (coords[0] <= x + w) \
                    and (y <= coords[1]) and (coords[1] <= y + h):
                return clickable
        return None

    def on_new_coords(self, x, y):
        """
        Takes on any cursor-related actions when the new
        coordinates arrive. Moves cursor, manages widgets
        highlight, selects widgets if hovered for long enough.

        :param x: new x coordinate, in pixels, float.
        :param y: new y coordinate, in pixels, float.

        :return: False, in order to avoid this function being called
        again automatically, what otherwise would be the case as
        long as this function is registered as a Clutter timeout callback
        from another Python thread for the sake of better Python-threads
        vs Clutter-GUI cooperation.
        """
        coords = (x, y)
        self.update_sprite(coords)
        actor = self.find_actor(coords)
        if actor is not None:
            if actor == self.hover_actor:
                if time.time() - self.hover_start > self._timeout:
                    actor.emit("clicked")
                    self.hover_start = time.time() + 1.0 # dead time
            else:
                # reset timeout
                if self.hover_actor is not None:
                    self.hover_actor.disable_hilite()
                self.hover_actor = actor
                self.hover_actor.enable_hilite()
                self.hover_start = time.time()
        else:
            if self.hover_actor is not None:
                self.hover_actor.disable_hilite()
                self.hover_actor = None
        return False

    def on_new_data(self, data):
        """
        Receives new raw data, parses them and schedules
        calling the main thread callback.

        :param data: raw data.
        """
        x, y = self.parse_coords(data)
        Clutter.threads_add_timeout(-100, 20, self.on_new_coords, x, y)

    def run(self, container):
        """
        Displays and starts the sprite. Runs proper
        tracker websocket client.

        :param container: widget that the sprite should be placed above.
        """
        self.container = container
        self._connect_rescan()
        self._rescan()
        self.container.insert_child_above(self, None)
        self.update_sprite(self.initial_position)
        self._running = True
        self.tracker_client.activate()

    def stop(self):
        """
        Stops the sprite. Stops the websocket client.
        """
        self._running = False
        self.tracker_client.deactivate()
        self.container.remove_child(self)
        self._disconnect_rescan()
        self.container = None
        self.hover_actor = None

    def is_running(self):
        """
        Checks whether the sprite is in a working state.

        :return: boolean.
        """
        return self._running
