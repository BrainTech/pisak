"""
Basic implementation of sliding page widget.
"""
import threading
import itertools
from math import ceil
from collections import OrderedDict
from functools import total_ordering

from gi.repository import Clutter, GObject

import pisak
from pisak import res, logger, exceptions, properties, scanning, layout, \
    unit, configurator, unit


_LOG = logger.get_logger(__name__)


@total_ordering
class DataItem:
    """
    Single data item that can be put on a `data` list owned by
    a `DataSource` instance. Data items are then used to produce some
    full-feature widgets or other objects managed by an application.
    Data items can be compared with each another and thus can be sorted.

    :param content: proper data content.
    :param cmp_key: key used for comparisons.
    """

    def __init__(self, content, cmp_key, flags=None):
        self.content = content
        self.cmp_key = cmp_key
        self.flags = flags or {}  # extra flags that can be set on a data item

    def _is_valid_operand(self, other):
        return isinstance(other, DataItem)

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplementedError
        return self.cmp_key < other.cmp_key

    def __bool__(self):
        return bool(self.content)


class LazyWorker:
    """
    Lazy worker class. Loads data in a separate thread.
    """

    def __init__(self, src):
        self._src = src

        self._step = 10

        self._worker = None
        self._running = True

    def _lazy_work(self):
        """
        Main worker function that loads all the data at once, in small portions.
        Each portion is '_step' number of elements long. Loads one
        portion of elements with identifiers from the front
        of the ids list and one portion from the back, in turns.
        """
        if self._src.lazy_offset is not None:
            any_left = True
            while any_left and self._running:
                any_left = self._load_portion_by_number(
                    self._src.lazy_offset, self._step)
                self._src.lazy_offset += self._step
        else:
            flat = list(range(0, len(self._src._ids), self._step))
            half_len = int(len(flat)/2)
            mixed = [idx for idx in itertools.chain(*itertools.zip_longest(
                flat[ :half_len], reversed(flat[half_len: ]))) if idx is not None]
            for idx in mixed:
                if not self._running:
                    break
                self._load_portion_by_ids(ids=self._src._ids[idx : idx+self._step])

    def _load_portion_by_ids(self, ids):
        """
        Load some portion of data items with the given identifiers.

        :param ids: list of ids specifying which data items should be loaded.
        """
        self._src._lazy_data.update(list(zip(map(str, ids),
                                    self._src._query_portion_of_data(ids))))
        self._src.data = self._src.produce_data(
            [(val, None) for val in list(self._src._lazy_data.values())],
            self._src._data_sorting_key)

    def _load_portion_by_number(self, offset, number):
        data = self._src._query_portion_of_data_by_number(offset, number)
        if data:
            ids = list(range(offset, offset + len(data)))
            self._src._lazy_data.update(list(zip(map(str, ids), data)))
            self._src.data = self._src.produce_data(
                [(val, None) for val in list(self._src._lazy_data.values())],
                self._src._data_sorting_key
            )
        return data

    @property
    def step(self):
        """
        Integer, number of data items loaded at each step.
        After setting this, data is started to being loaded.
        """
        return self._step

    @step.setter
    def step(self, value):
        self._step = value

    def stop(self):
        """
        Stop the loader, stop any on-going activities.
        """
        self._running = False
        if self._worker is not None:
            if self._worker.is_alive():
                self._worker.join()
            self._worker = None

    def start(self):
        """
        Start the loader.
        """
        self._running = True
        if not self._worker:
            self._worker = threading.Thread(target=self._lazy_work,
                                                        daemon=True)
            self._worker.start()
        else:
            _LOG.warning('Lazy loader has been started already.')


class DataSource(GObject.GObject, properties.PropertyAdapter,
                 configurator.Configurable):
    """
    Base class for the PISAK data sources.

    It can work in a `lazy_loading` mode of operation by setting this property
    to True. However, it should be noted that only few of all the
    methods are compatible with the 'lazy' mode and are able to take
    advantage of the functionality it provides.
    So far, these are: `get_items_forward` and `get_items_backward`.
    Before enabling the 'lazy' mode, there should also be certain things
    supplied by a child class.
    """
    __gtype_name__ = "PisakDataSource"
    __gsignals__ = {
        "data-is-ready": (
            GObject.SIGNAL_RUN_FIRST, None, ()),
        "length-changed": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_INT64,)),
        'reload': (
            GObject.SIGNAL_RUN_FIRST, None, ())
    }

    __gproperties__ = {
        "item_ratio_width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "item_ratio_height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "item_ratio_spacing": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "item_preview_ratio_width": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "item_preview_ratio_height": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "custom_topology": (
            GObject.TYPE_BOOLEAN,
            "", "", False,
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        self._length = 0
        self._lazy_loading = False
        self.page_idx = None
        self.custom_topology = False
        self.from_idx = 0
        self.to_idx = 0
        self.data_sets_count = 0
        self.data_generator = None
        self._target_spec = None
        self._data = []
        self._data_set_idx = None
        self.item_handler = None
        self._data_sorting_key = None
        # synchronization for an access to the `data` buffer.
        self._lock = threading.RLock()
        # something to do when new data is available..
        self.on_new_data = None
        self.data_sets_ids_list = None

        self._init_lazy_props()

        self.apply_props()

    @property
    def target_spec(self):
        """
        Specification of a target that the `DataSource` serves as a data supplier for.
        If the lazy loading mode is on then the lazy loader is triggered here.
        """
        return self._target_spec

    @target_spec.setter
    def target_spec(self, value):
        self._target_spec = value

        if self.lazy_loading:
            self._lazy_loader.step = value['columns'] * value['rows']
            self._lazy_loader.start()

    @property
    def custom_topology(self):
        """
        Whether the custom topology mode of the elements positioning
        should be applied, boolean.
        """
        return self._custom_topology

    @custom_topology.setter
    def custom_topology(self, value):
        self._custom_topology = value

    @property
    def item_ratio_spacing(self):
        """
        Value relative to the item width/height.
        """
        return self._item_ratio_spacing

    @item_ratio_spacing.setter
    def item_ratio_spacing(self, value):
        self._item_ratio_spacing = value

    @property
    def item_ratio_height(self):
        """
        Item widget height, as a fraction of the whole screen height.
        """
        return self._item_ratio_height

    @item_ratio_height.setter
    def item_ratio_height(self, value):
        self._item_ratio_height = value

    @property
    def item_ratio_width(self):
        """
        Item widget width, as a fraction of the whole screen width.
        """
        return self._item_ratio_width

    @item_ratio_width.setter
    def item_ratio_width(self, value):
        self._item_ratio_width = value

    @property
    def item_preview_ratio_height(self):
        """
        Value relative to the item height.
        """
        return self._item_preview_ratio_height

    @item_preview_ratio_height.setter
    def item_preview_ratio_height(self, value):
        self._item_preview_ratio_height = value

    @property
    def item_preview_ratio_width(self):
        """
        Value relative to the item width.
        """
        return self._item_preview_ratio_width

    @item_preview_ratio_width.setter
    def item_preview_ratio_width(self, value):
        self._item_preview_ratio_width = value

    @property
    def data_set_idx(self):
        """
        Idx of the current data set.
        """
        return self._data_set_idx

    @data_set_idx.setter
    def data_set_idx(self, value):
        self._data_set_idx = value
        if self.data_generator is not None:
            if self.data_sets_ids_list and value <= \
                    len(self.data_sets_ids_list):
                value = self.data_sets_ids_list[value-1]
            elif value <= self.data_sets_count:
                pass
            else:
                return  # invalid params for the data generator

            self.data = self.data_generator(value)

    @property
    def data(self):
        """
        List of some arbitrary data items. Each single item should
        be an instance of the `DataItem` class.
        """
        with self._lock:
            return self._data.copy()

    @data.setter
    def data(self, value):
        with self._lock:
            self._data = value
            self._length = len(value)
        self.emit('length-changed', self._length)
        self.emit("data-is-ready")

    def reload(self):
        """
        Reload.
        """
        self.emit('reload')

    @property
    def length(self):
        """
        Total length of the whole available data set.
        """
        return self._length

    def _generate_items_normal(self):
        """
        Generate items and structure them into a nested list.
        """
        data = self.data
        rows, cols = self.target_spec["rows"], self.target_spec["columns"]
        to = self.to_idx
        if self.from_idx + rows*cols >= self._length:
            to = self.from_idx + rows*cols
        items = []
        idx = 0
        for index in range(self.from_idx, to):
            if idx % cols == 0:
                row = []
                items.append(row)
            idx += 1
            if index < self._length and index < self.to_idx:
                item = self._produce_item(data[index])
            elif index > self._length or index >= self.to_idx:
                item = Clutter.Actor()
                self._prepare_filler(item)
            self._prepare_item(item)
            row.append(item)
        return items

    def _generate_items_flat(self):
        """
        Generate items and place them all into a flat list.
        """
        items = []
        for index in range(self.from_idx, self.to_idx):
            if index < self._length:
                item = self._produce_item(self.data[index])
                self._prepare_item(item)
                items.append(item)
        return items

    def _prepare_item(self, item):
        """
        Adjust the given item according to the target specification in order
        to fit its space. If no target specification is set then nothing
        happens. Then, set all the proper attributes of the item.

        :param item: single item generated from data
        """
        if self.target_spec is not None:
            columns = self.target_spec["columns"]
            rows = self.target_spec["rows"]
            target_spacing = self.target_spec["spacing"]
            item_width = (self.target_spec["width"] - (columns-1) *
                          target_spacing) / columns
            item_height = (self.target_spec["height"] - (rows-1) *
                           target_spacing) / rows
            item.set_size(item_width, item_height)

        for prop in ("item_ratio_width", "item_ratio_height",
                     "item_ratio_spacing", "item_preview_ratio_width",
                     "item_preview_ratio_height"):
            if hasattr(self, prop):
                value = getattr(self, prop)
                if prop in ("item_ratio_width" or "item_ratio_height"):
                    setattr(item, prop.strip("item_"), value)
                if prop == "ratio_spacing" and hasattr(item, "box"):
                    setattr(item.box, "spacing", value * item.get_height())
                elif prop == "preview_ratio_width" and hasattr(item, "preview"):
                    setattr(item.preview, "width", value * item.get_width())
                elif prop == "preview_ratio_height" and hasattr(item, "preview"):
                    setattr(item.preview, "height", value * item.get_width())

    def _produce_item(self, data_item):
        raise NotImplementedError

    def _prepare_filler(self, filler):
        filler.set_background_color(Clutter.Color.new(255, 255, 255, 0))

    def query_items_forward(self, count):
        """
        Query a given number of forward items generated from data.
        Method is compatible with a normal topology mode but NOT with
        a custom one. Data items are picked from a flat data list.

        :param count: number of items to be returned.

        :return: list of data items or None if in the lazy loading mode.
        """
        self.from_idx = self.to_idx % self._length if \
                            self._length > 0 else 0
        self.to_idx = min(self.from_idx + count, self._length)

        if self.lazy_loading:
            self._schedule_sending_data(1)
        else:
            return self._generate_items_normal()

    def query_items_backward(self, count):
        """
        Query a given number of backward items generated from data.
        Method is compatible with a normal topology mode but NOT with
        a custom one. Data items are picked from a flat data list.

        :param count: number of items to be returned.

        :return: list of data items or None if in the lazy loading mode.
        """ 
        rows, cols = self.target_spec["rows"], self.target_spec["columns"]
        self.to_idx = self.from_idx or self._length
        if self.to_idx < count:
            self.from_idx = self._length - count + self.to_idx
        elif self.to_idx == self._length and self._length % (rows*cols) != 0:
            self.from_idx = self.to_idx - (self._length % (rows*cols))
        else:
            self.from_idx = self.to_idx - count

        if self.lazy_loading:
            self._schedule_sending_data(-1)
        else:
            return self._generate_items_normal()

    def next_data_set(self):
        """
        Move to the next data set if available.
        """
        if self.data_set_idx is not None:
            self.data_set_idx = self.data_set_idx + 1 if \
                               self.data_set_idx < self.data_sets_count else 1

    def previous_data_set(self):
        """
        Move to the previous data set if avalaible.
        """
        if self.data_set_idx is not None:
            self.data_set_idx = self.data_set_idx - 1 if \
                               self.data_set_idx > 1 else self.data_sets_count

    def get_all_items(self):
        """
        Get all items from the current data set. Method compatible with
        default topology mode of operation.
        """
        self.from_idx = 0
        self.to_idx = self._length
        return self._generate_items_flat()

    def produce_data(self, raw_data, cmp_key_factory):
        """
        Generate list of `DataItems` out of some arbitrary raw data.
        Produced list can be then used as the `data`. If some given
        raw data item is None then it will remain None on a target list.

        :param raw_data: container with tuples, each consisting of a
        raw data item and dictionary of flags specific to this item.
        :param cmp_key_factory: function to retrieve some comparison
        key out of a given data item.

        :return: list of `DataItems`.
        """
        return sorted([DataItem(item, cmp_key_factory(item), flags) for
                       item, flags in raw_data])

    def clean_up(self):
        """
        Clean after any activities of the data source.
        """
        if self.lazy_loading:
            self._clean_up_lazy()

    # ----------------------- LAZY LOADING METHODS ---------------------- #

    def _init_lazy_props(self):
        """
        Initialize all the properties specific to the lazy loader.
        """
        self._lazy_loading = False

        # buffer for storing already, lazily, loaded data.
        self._lazy_data = OrderedDict()
        # list of data identifiers, specific for a given data supplier.
        self._ids = []
        # offset for lazy data
        self.lazy_offset = None

        # main lazy loading worker.
        self._lazy_loader = LazyWorker(self)

    @property
    def lazy_loading(self):
        """
        Switch the lazy loading mode - can be set True or False,
        default is False. In the lazy loading mode, data source will
        load only some limited portion of a given data at a time;
        automatically load data that will probably be needed in
        the future queries; store the already loaded data
        in a proper order for a future use.
        """
        return self._lazy_loading

    @lazy_loading.setter
    def lazy_loading(self, value):
        self._lazy_loading = value
        if value:
            self._set_up_lazy_loading()

    def _query_portion_of_data(self, ids):
        """
        Query the data provider for a portion of data with the given ids.
        Should be implemented by child.

        :params: ids: list of data identifiers.

        :return: list of data items.
        """
        raise NotImplementedError

    def _query_portion_of_data_by_number(self):
        raise NotImplementedError

    def _query_ids(self):
        """
        Query the data provider for a list of all the available data ids.
        Should be implemented by child.

        :return: list of ids.
        """
        raise NotImplementedError

    def _set_up_lazy_loading(self):
        """
        Initialize all the necessary things and set up the lazy loader.
        Should be always called on the lazy loader init.
        """
        self._check_ids_range()

    def _check_ids_range(self):
        """
        Query to the data supplier for a list of identifiers of all the
        available data. Update the `_lazy_data` container with previously
        non-existing ids and prepare placeholders for data
        items with these ids, that will be loaded later.
        Update the main `data` buffer.
        """
        self._ids = self._query_ids()
        self._lazy_data.update(
            [(str(ide), None) for ide in self._ids if
             str(ide) not in self._lazy_data])
        self.data = [None for _ in self._lazy_data]

    def _schedule_sending_data(self, direction):
        """
        Schedule sending the data as soon as it is available.
        Data should be loaded in a background.

        :param direction: -1 or 1, that is whether data should be
        sent from backward or forward.
        """
        Clutter.threads_add_timeout(0, 100, self._send_data, direction)

    def _send_data(self, direction):
        """
        Send the data somewhere.

        :param direction: data in which direction should be sent.

        :return: True when no data available or False after sending the data.
        """
        if self._has_data(direction):
            if not callable(self.on_new_data):
                raise exceptions.PisakException(
                    'No data receiver has been declared.')
            try:
                self.on_new_data(self._generate_items_normal())
            except TypeError as exc:
                _LOG.error(exc)
                raise
            return False
        else:
            return True

    def _has_data(self, direction):
        """
        Check if there is a portion of data available, in the given direction.
        Data is checked with some offset, just to be sure, in a case when some
        indexing has been messed up.

        :param direction: -1 or 1, that is whether data should be
        checked backward or forward.

        :return: True or False
        """
        offset = self._lazy_loader.step
        if direction == -1:
            from_idx = max(self.from_idx - offset, 0)
            to_idx = self.to_idx
        elif direction == 1:
            from_idx = self.from_idx
            to_idx = min(self.to_idx + offset, self._length)
        else:
            raise ValueError('Invalid direction. Must be -1 or 1.')

        return to_idx <= len(self.data) and all(self.data[from_idx : to_idx])

    def _clean_up_lazy(self):
        """
        Take any actions necessary for cleaning after the lazy loader.
        """
        self._lazy_loader.stop()

    def get_data_ids_list(self):
        """
        Get list of identifiers of all the data items.
        """
        return self._ids.copy()

    # ----------------- END OF LAZY LOADING METHODS ------------------ #


class _Page(scanning.Group):
    """
    Page widget supplied to pager as its content.
    """

    def __init__(self, items, spacing, strategy, sound, row_sounds):
        super().__init__()
        self.items = []  # flat container for the page content
        self.strategy = strategy
        self.sound = sound
        self.row_sounds = row_sounds
        self.layout = Clutter.BoxLayout()
        self.layout.set_spacing(spacing)
        self.layout.set_orientation(Clutter.Orientation.VERTICAL)
        self.set_layout_manager(self.layout)
        self.set_y_align(Clutter.ActorAlign.START)
        self._add_items(items, spacing)

    def _add_items(self, items, spacing):
        for index, row in enumerate(items):
            group = scanning.Group()
            group.strategy = scanning.RowStrategy()
            try:
                group.sound = self.row_sounds[index]
            except IndexError:
                group.sound = str(index + 1) if index + 1 < 10 else 'scan'
            group.strategy.unwind_to = self.strategy.unwind_to or self
            group.strategy.max_cycle_count = self.strategy.max_cycle_count
            group.strategy.interval = self.strategy.interval
            group_box = layout.Box()
            group_box.spacing = spacing
            group.add_child(group_box)
            self.add_child(group)
            for item in row:
                group_box.add_child(item)
                self.items.append(item)

    def adjust_content(self):
        """
        Adjust content of the page using any internal settings
        held by the items themselves. Before adjusting, one should ensure
        that page is already aware of its parent and whole environment.

        As for now, any adjusting specifications to be applied should be
        stored by an item itself and exposed by 'adjust' method.
        """
        for item in self.items:
            if hasattr(item, "adjust") and callable(item.adjust):
                item.adjust()


class PagerWidget(layout.Bin, properties.PropertyAdapter,
                  configurator.Configurable):
    """
    Pisak generic pager widget.
    Display elements placed on pages.
    Display only one page at time and is responsible for flipping them.
    """

    __gtype_name__ = "PisakPagerWidget"
    __gsignals__ = {
        "progressed": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_FLOAT, GObject.TYPE_INT64)),
        "value-changed": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_INT64, GObject.TYPE_INT64)),
        "limit-declared": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_INT64,)),
        "ready": (
            GObject.SIGNAL_RUN_FIRST, None, ())
    }
    __gproperties__ = {
        "data-source": (
            DataSource.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "rows": (
            GObject.TYPE_UINT, "", "", 1,
            GObject.G_MAXUINT, 4, GObject.PARAM_READWRITE),
        "columns": (
            GObject.TYPE_UINT, "", "", 1,
            GObject.G_MAXUINT, 3, GObject.PARAM_READWRITE),
        "page-strategy": (
            scanning.Strategy.__gtype__, "", "",
            GObject.PARAM_READWRITE),
        "page_ratio_spacing": (
            GObject.TYPE_FLOAT, None, None, 0, 1., 0,
            GObject.PARAM_READWRITE),
        "sound": (
            GObject.TYPE_STRING,
            "", "", "scan",
            GObject.PARAM_READWRITE),
        "row-sounds": (
            GObject.TYPE_STRING, None, None, '',
            GObject.PARAM_READWRITE
        ),
        "idle-duration": (
            GObject.TYPE_INT64, "idle duration",
            "duration of one page exposition", 0,
            GObject.G_MAXUINT, 5000, GObject.PARAM_READWRITE),
        "transition-duration": (
            GObject.TYPE_INT64, "transition duration",
            "duration of page transition", 0,
            GObject.G_MAXUINT, 1000, GObject.PARAM_READWRITE)            
    }

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.set_clip_to_allocation(True)
        self.page_index = 0
        self._page_count = 1
        self.page_spacing = 0
        self._current_direction = 0
        self.old_page_transition = Clutter.PropertyTransition.new("x")
        self.new_page_transition = Clutter.PropertyTransition.new("x")
        self.new_page_transition.connect("stopped", self._clean_up)
        self.connect("notify::mapped", lambda *_: self._show_initial_page())
        self._sound = 'scan'
        self._row_sounds = ''
        self.idle_duration = 3000
        self.transition_duration = 1000
        self._data_source = None
        self._inited = False
        self._page_strategy = None
        self._idle_duration = 0
        self._page_ratio_spacing = 0
        self._ready = False
        self._rows = 3
        self._columns = 4
        self._current_page = None
        self.old_page = None
        self.apply_props()

    @property
    def page_count(self):
        """
        Total number of pages.
        """
        return self._page_count

    @page_count.setter
    def page_count(self, value):
        self._page_count = value
        self.emit('value-changed', self.page_index+1, value)

    @property
    def sound(self):
        """
        Sound specific for the pager.
        """
        return self._sound

    @sound.setter
    def sound(self, value):
        self._sound = value

    @property
    def row_sounds(self):
        """
        List of sounds specific for consecutive rows on a page.
        Common for all pages.
        """
        return self._row_sounds

    @row_sounds.setter
    def row_sounds(self, value):
        self._row_sounds = [sound.strip() for sound in value.split(',')]

    @property
    def page_strategy(self):
        """
        Scanning strategy. :see: :module:`pisak.scanning`
        """
        return self._page_strategy

    @page_strategy.setter
    def page_strategy(self, value):
        self._page_strategy = value

    @property
    def page_ratio_spacing(self):
        """
        Distance between neighbouring items on a page, as a fraction of the whole
        screen width/height.
        """
        return self._page_ratio_spacing

    @page_ratio_spacing.setter
    def page_ratio_spacing(self, value):
        self._page_ratio_spacing = value
        self.page_spacing = int(min(unit.h(value), unit.w(value)))

    @property
    def data_source(self):
        """
        :class:`DataSource` instance.
        """
        return self._data_source

    @data_source.setter
    def data_source(self, value):
        self._data_source = value
        if value is not None:
            value.on_new_data = self.on_new_items
            self.connect('destroy', lambda *_: value.clean_up)
            value.connect("data-is-ready", lambda *_:
                          self._show_initial_page())
            value.connect('length-changed', lambda _, length:
                          self._calculate_page_count(length))
            value.connect('reload', lambda *_: self._reload())

    @property
    def rows(self):
        """
        Number of rows.
        """
        return self._rows
    
    @rows.setter
    def rows(self, value):
        self._rows = value
    
    @property
    def columns(self):
        """
        Number of columns.
        """
        return self._columns
    
    @columns.setter
    def columns(self, value):
        self._columns = value

    @property
    def idle_duration(self):
        """
        Idle before flipping to the next page,
        applies in the automatic flipping mode.
        """
        return self._idle_duration

    @idle_duration.setter
    def idle_duration(self, value):
        self._idle_duration = value

    @property
    def transition_duration(self):
        """
        Duration of an animation showing a page
        sliding from one side to the middle of the screen.
        """
        return self.new_page_transition.get_duration()

    @transition_duration.setter
    def transition_duration(self, value):
        self.new_page_transition.set_duration(value)
        self.old_page_transition.set_duration(value)

    @property
    def ready(self):
        """
        Whether the pager is ready to work, boolean.
        """
        return self._ready

    @ready.setter
    def ready(self, value):
        self._ready = value
        if value:
            self.emit('ready')

    def _calculate_page_count(self, data_length):
        """
        Calculate the total number of pages in the pager, based on the
        length of data being supplied by the data source.

        :param data_length: length of a data buffer.
        """
        if self.data_source.custom_topology:
            self.page_count = data_length
        else:
            self.page_count = ceil(data_length /
                                   (self.rows*self.columns))

    def _introduce_new_page(self, items):
        """
        Method for adding and displaying new page and disposing of the old one.
        When 'direction' is 0 then adjusting the content of the new page happens
        immediately, otherwise it is performed in the `_clean_up` method when
        any page transitions are already over.

        :param items: list of items to be placed on the new page.
        """
        _new_page = _Page(items, self.page_spacing, self.page_strategy,
                          self.sound, self.row_sounds)
        direction = self._current_direction
        if direction == 0:
            self._current_page = _new_page
            self._current_page.set_id(self.get_id() + "_page")
            self.add_child(self._current_page)
            self._current_page.adjust_content()
        else:
            self.old_page = self._current_page
            new_page_from = self.old_page.get_x() + direction * \
                self.old_page.get_width()
            new_page_to = self.old_page.get_x()
            old_page_to = self.old_page.get_x() - direction * \
                self.old_page.get_width()
            self._current_page = _new_page
            self._current_page.set_id(self.get_id() + "_page")
            self._current_page.set_x(new_page_from)
            self.add_child(self._current_page)
            self.new_page_transition.set_from(new_page_from)
            self.new_page_transition.set_to(new_page_to)
            self.old_page_transition.set_to(old_page_to)
            self.old_page.add_transition("x", self.old_page_transition)
            self._current_page.add_transition("x", self.new_page_transition)
        if self._page_count > 0:
            self.emit('value-changed', self.page_index+1, self._page_count)
        else:
            self.emit("value-changed", 0, 0)

    def _reload(self):
        """
        Enforce reloading.
        """
        if self._current_page in self.get_children():
            self.remove_child(self._current_page)
        self.page_index = 0
        self._show_initial_page(True)

    def _show_initial_page(self, enforce=False):
        """
        Display pager initial page.
        """
        if enforce or \
                not self._inited and \
                self.data_source is not None and \
                self._current_page is None:
            self._inited = True
            # create page specification needed for proper items adjustment
            self.data_source.target_spec = {"width": self.get_width(),
                                            "height": self.get_height(),
                                            "spacing": self.page_spacing,
                                            "rows": self.rows,
                                            "columns": self.columns}
            self._current_direction = 0
            if self.data_source.custom_topology:
                items = self.data_source.get_items_custom_next()
            else:
                items = self.data_source.query_items_forward(
                    self.rows*self.columns)
            self._calculate_page_count(self.data_source.length)
            if items:
                self._introduce_new_page(items)
            self.ready = True

    def _automatic_timeout(self, _data):
        """
        Handler function for the automatic page flipping timeout.
        """
        if self.is_running:
            self.next_page()
            return True
        else:
            return False

    def _clean_up(self, _source, _event):
        """
        Func used as a signal handler. Clean up after stoppage of the
        new page 'x' transition. Remove transitions and
        free the old page.
        """
        self._current_page.adjust_content()
        self._current_page.remove_transition("x")
        self.old_page.remove_transition("x")
        if self.old_page is not None:
            if self.contains(self.old_page):
                self.remove_child(self.old_page)
        self.old_page = None

    def scan_page(self):
        """
        Start scanning the current page.
        """
        pisak.app.window.pending_group = self._current_page
        self._current_page.start_cycle()

    def on_new_items(self, items):
        """
        Receive new items.

        :param items: list of items.
        """
        self._introduce_new_page(items)

    def next_page(self):
        """
        Move to the next page.
        """
        if self.old_page is None and self._page_count > 1:
            self.page_index = self.data_source.page_idx if \
                self.data_source.page_idx is not None else \
                (self.page_index+1) % self._page_count
            self._current_direction = 1
            if self.data_source.custom_topology:
                items = self.data_source.get_items_custom_next()
            else:
                items = self.data_source.query_items_forward(
                    self.rows * self.columns)
            if items:
                self._introduce_new_page(items)

    def previous_page(self):
        """
        Move to the previous page.
        """
        if self.old_page is None and self._page_count > 1:
            self.page_index = self.data_source.page_idx if \
                self.data_source.page_idx is not None else (
                    self.page_index - 1 if self.page_index >= 1 \
                    else self._page_count - 1)
            self._current_direction = -1
            if self.data_source.custom_topology:
                items = self.data_source.get_items_custom_previous()
            else:
                items = self.data_source.query_items_backward(
                    self.columns * self.rows)
            if items:
                self._introduce_new_page(items)

    def run_automatic(self):
        """
        Start automatic page flipping.
        """
        if self._page_count > 1:
            self.is_running = True
            Clutter.threads_add_timeout(0, self.idle_duration,
                                        self._automatic_timeout, None)

    def stop_automatic(self):
        """
        Stop automatic page flipping.
        """
        self.is_running = False


class PageFlip(scanning.Group):
    """
    A one-purpose only mechanism, wrapped into artificial scanning group,
    instantaneously flips a pager page when started.
    """
    __gtype_name__ = "PisakPageFlip"

    __gproperties__ = {
        "target": (PagerWidget.__gtype__, "", "", GObject.PARAM_READWRITE),
    }

    def __init__(self):
        self._target = None
        super().__init__()

    @property
    def target(self):
        """
        :class:`PagerWidget` instance.
        """
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def start_cycle(self):
        """
        Reimplementation of the generic scanning group method.
        Flips the target pager page and schedules the start
        of the page scanning cycle.
        """
        if self._target is not None:
            self._target.next_page()
            Clutter.threads_add_timeout(0, self._target.transition_duration,
                                        lambda *_: self._target.scan_page(),
                                        None)
        else:
            _LOG.warning("PageFlip without target: " + self.get_id())
