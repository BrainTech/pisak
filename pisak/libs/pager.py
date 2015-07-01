'''
Basic implementation of sliding page widget.
'''
from math import ceil
from functools import total_ordering

from gi.repository import Clutter, GObject
from pisak import res, logger
from pisak.libs import properties, scanning, layout, unit, configurator, unit

_LOG = logger.get_logger(__name__)


@total_ordering
class DataItem:
    """
    Single data item that can be put on a `data` list owned by
    a `DataSource` instance. Data items are then used to produce some
    full-feature widgets or other objects managed by an application.
    Data items can be compared with each another and thus can be sorted.

    :param content: proper data content.
    :param cmp_key: key used for comparisions.
    """
    def __init__(self, content, cmp_key):
        self.content = content
        self.cmp_key = cmp_key
        self.flags = {}  # extra flags that can be set on a data item

    def _is_valid_operand(self, other):
        return isinstance(other, DataItem)

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplementedError
        return self.cmp_key < other.cmp_key


class DataSource(GObject.GObject, properties.PropertyAdapter,
                 configurator.Configurable):
    """
    Base class for Pisak data sources.
    """
    __gtype_name__ = "PisakDataSource"
    __gsignals__ = {
        "data-is-ready": (GObject.SIGNAL_RUN_FIRST, None, ())
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
        self.custom_topology = False
        self.from_idx = 0
        self.to_idx = 0
        self.data_length = 0
        self.data_sets_count = 0
        self.data_generator = None
        self.target_spec = None  # specification of the data's target
        self.data = None
        self.data_set_id = None
        self.item_handler = None
        self.apply_props()

    @property
    def custom_topology(self):
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
        return self._item_ratio_height

    @item_ratio_height.setter
    def item_ratio_height(self, value):
        self._item_ratio_height = value

    @property
    def item_ratio_width(self):
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
    def data_set_id(self):
        return self._data_set_id

    @data_set_id.setter
    def data_set_id(self, value):
        self._data_set_id = value
        if value is not None and self.data_generator is not None and \
           value <= self.data_sets_count:
            self.data = self.data_generator(value)

    @property
    def data(self):
        """
        List of some arbitrary data items. Each single item should be an instance
        of the `DataItem` class.
        """
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        if value is not None:
            self.data_length = len(value)
            self.emit("data-is-ready")

    def _generate_items_normal(self):
        """
        Generate items and structure them into a nested list.
        """
        rows, cols = self.target_spec["rows"], self.target_spec["columns"]
        to = self.to_idx
        if self.from_idx + rows*cols >= self.data_length:
            to = self.from_idx + rows*cols
        items = []
        idx = 0
        for index in range(self.from_idx, to):
            if idx % cols == 0:
                row = []
                items.append(row)
            idx += 1
            if index < self.data_length and index < self.to_idx:
                item = self._produce_item(self.data[index])
            elif index > self.data_length or index >= self.to_idx:
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
            if index < self.data_length:
                item = self._produce_item(self.data[index])
                self._prepare_item(item)
                items.append(item)
        return items

    def _generate_items_custom(self, part):
        """
        Generate items from the given subset of the data.
        Data should be already properly structured.

        :param part: number of subset of the set of all data items
        """
        data = self.data[part]
        self.target_spec["columns"] = len(data[0]) # custom number of columns
        self.target_spec["rows"] = len(data) # custom number of rows
        items = []
        for row in data:
            items_row = []
            for record in row:
                if record:
                    item = self._produce_item(record)
                else:
                    item = Clutter.Actor()
                    self._prepare_filler(item)
                self._prepare_item(item)
                items_row.append(item)
            items.append(items_row)
        return items

    def _generate_items(self, part=None):
        """
        Generate items using a method relevant to the current
        kind of topology.

        :param part: number of subset of the set of all data items or None
        """
        if self.custom_topology:
           return self._generate_items_custom(part)
        else:
            return self._generate_items_normal()

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

    def get_items_forward(self, count):
        """
        Return given number of forward items generated from data.
        Method is compatible with a normal topology mode but NOT with
        a custom one. Data items are picked from a flat data list.

        :param count: number of items to be returned
        """
        self.from_idx = self.to_idx % self.data_length if \
                        self.data_length > 0 else 0
        self.to_idx = min(self.from_idx + count, self.data_length)
        return self._generate_items_normal()

    def get_items_backward(self, count):
        """
        Return given number of backward items generated from data.
        Method is compatible with a normal topology mode but NOT with
        a custom one. Data items are picked from a flat data list.

        :param count: number of items to be returned
        """
        rows, cols = self.target_spec["rows"], self.target_spec["columns"]
        self.to_idx = self.from_idx or self.data_length
        if self.to_idx < count:
            self.from_idx = self.data_length - count + self.to_idx
        elif self.to_idx == self.data_length and self.data_length % (rows*cols) != 0:
            self.from_idx = self.to_idx - (self.data_length % (rows*cols))
        else:
            self.from_idx = self.to_idx - count
        return self._generate_items_normal()

    def next_data_set(self):
        """
        Move to the next data set if avalaible.
        """
        if self.data_set_id is not None:
            self.data_set_id = self.data_set_id + 1 if \
                               self.data_set_id < self.data_sets_count else 1

    def previous_data_set(self):
        """
        Move to the previous data set if avalaible.
        """
        if self.data_set_id is not None:
            self.data_set_id = self.data_set_id - 1 if \
                               self.data_set_id > 1 else self.data_sets_count

    def get_all_items(self):
        """
        Get all items from the current data set. Method compatible with
        default topology mode of operation.
        """
        self.from_idx = 0
        self.to_idx = self.data_length
        return self._generate_items_flat()

    def get_items_custom(self, part):
        """
        Get all items from the given page. Method compatible with
        custom topology mode of operation.

        :param part: which part of all items (e.g items from which page)
        should be returned. Usually items that belong to the same part are
        packed into a single list. 

        :returns: list of items packed into lists
        """
        return self._generate_items_custom(part)

    def produce_data(self, raw_data, cmp_key_factory):
        """
        Generate list of `DataItems` out of some arbitrary raw data. Produced list
        can be then used as the `data`.

        :param raw_data:container with some raw data items.
        :param cmp_key_factory: function to get some comparision
        key out of a data item.

        :return: list of `DataItems`.
        """
        return [DataItem(item, cmp_key_factory(item)) for item in raw_data]


class _Page(scanning.Group):
    """
    Page widget supplied to pager as its content.
    """
    def __init__(self, items, spacing, strategy, width, height):
        super().__init__()
        self.items = []  # flat container for the page content
        self.strategy = strategy
        self.layout = Clutter.BoxLayout()
        self.layout.set_spacing(spacing)
        self.layout.set_orientation(Clutter.Orientation.VERTICAL)
        self.set_layout_manager(self.layout)
        self.set_y_align(Clutter.ActorAlign.START)
        self._add_items(items, spacing)

    def _add_items(self, items, spacing):
        for row in items:
            group = scanning.Group()
            group.strategy = scanning.RowStrategy()
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


class PagerWidget(layout.Bin, configurator.Configurable):
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
        "limit-declared": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_INT64,))
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
        self.pages_count = 1
        self.page_spacing = 0
        self.old_page_transition = Clutter.PropertyTransition.new("x")
        self.new_page_transition = Clutter.PropertyTransition.new("x")
        self.new_page_transition.connect("stopped", self._clean_up)
        self.connect("notify::mapped", lambda *_: self._show_initial_page())
        self.idle_duration = 3000
        self.transition_duration = 1000
        self._data_source = None
        self._page_strategy = None
        self._page_ratio_spacing = 0
        self._rows = 3
        self._columns = 4
        self._current_page = None
        self.old_page = None
        self.apply_props()

    @property
    def page_strategy(self):
        return self._page_strategy

    @page_strategy.setter
    def page_strategy(self, value):
        self._page_strategy = value

    @property
    def page_ratio_spacing(self):
        return self._page_ratio_spacing

    @page_ratio_spacing.setter
    def page_ratio_spacing(self, value):
        self._page_ratio_spacing = value
        self.page_spacing = int(min(unit.h(value), unit.w(value)))

    @property
    def data_source(self):
        return self._data_source

    @data_source.setter
    def data_source(self, value):
        self._data_source = value
        if value is not None:
            value.connect("data-is-ready",
                          lambda *_: self._show_initial_page())

    @property
    def rows(self):
        return self._rows
    
    @rows.setter
    def rows(self, value):
        self._rows = value
    
    @property
    def columns(self):
        return self._columns
    
    @columns.setter
    def columns(self, value):
        self._columns = value

    @property
    def idle_duration(self):
        return self._idle_duration

    @idle_duration.setter
    def idle_duration(self, value):
        self._idle_duration = value

    @property
    def transition_duration(self):
        return self.new_page_transition.get_duration()

    @transition_duration.setter
    def transition_duration(self, value):
        self.new_page_transition.set_duration(value)
        self.old_page_transition.set_duration(value)

    def _introduce_new_page(self, items, direction):
        """
        Method for adding and displaying new page and disposing of the old one.
        When 'direction' is 0 then adjusting the content of the new page happens
        immediately, otherwise it is performed in the `_clean_up` method when
        any page transisions are already over.

        :param items: list of items to be placed on the new page
        :param direction: which page should be introduced next.
        1 for the next page, -1 for the previous page and 0 for the initial one. 
        """
        _new_page = _Page(items, self.page_spacing,
                          self.page_strategy,
                          self.get_width(), self.get_height())

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

        if self.pages_count > 0:
            self.emit("progressed", float(self.page_index+1) \
                    / self.pages_count, self.page_index+1)
        else:
            self.emit("progressed", 0, 0)

    def _show_initial_page(self):
        """
        Display pager initial page.
        """
        if self.data_source is not None and \
           self.data_source.data is not None and \
           self._current_page is None:
            # create page specification needed for proper items adjustment
            self.data_source.target_spec = {"width": self.get_width(),
                        "height": self.get_height(),
                        "spacing": self.page_spacing,
                        "rows": self.rows, "columns": self.columns}
            if self.data_source.custom_topology:
                self.pages_count = len(self.data_source.data)
                items = self.data_source.get_items_custom(self.page_index)
            else:
                self.pages_count = ceil(self.data_source.data_length \
                                        / (self.rows*self.columns))
                items = self.data_source.get_items_forward(
                    self.rows*self.columns)
            self.emit("limit-declared", self.pages_count)
            self._introduce_new_page(items, 0)

    def _automatic_timeout(self, data):
        """
        Handler function for the automatic page flipping timeout.
        """
        if self.is_running:
            self.next_page()
            return True
        else:
            return False

    def _clean_up(self, source, event):
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

    def next_page(self):
        """
        Move to the next page.
        """
        if self.old_page is None and self.pages_count > 1:
            self.page_index = (self.page_index+1) % self.pages_count
            if self.data_source.custom_topology:
                items = self.data_source.get_items_custom(self.page_index)
            else:
                items = self.data_source.get_items_forward(
                    self.rows*self.columns)
            self._introduce_new_page(items, 1)

    def previous_page(self):
        """
        Move to the previous page.
        """
        if self.old_page is None and self.pages_count > 1:
            self.page_index = self.page_index - 1 if self.page_index >= 1 \
                                    else self.pages_count - 1
            if self.data_source.custom_topology:
                items = self.data_source.get_items_custom(self.page_index)
            else:
                items = self.data_source.get_items_backward(
                    self.columns * self.rows)
            self._introduce_new_page(items, -1)

    def run_automatic(self):
        """
        Start automatic page flipping.

        :deprecated: Use scanning instead
        """
        if self.pages_count > 1:
            self.is_running = True
            Clutter.threads_add_timeout(0, self.idle_duration,
                                    self._automatic_timeout, None)

    def stop_automatic(self):
        """
        Stop automatic page flipping.

        :deprecated: Use scanning instead
        """
        self.is_running = False


class PageFlip(scanning.Group):
    """
    A one-purpose only mechanism, wrapped into artificial scanning group,
    instantaneously flips a pager page when started.
    """
    __gtype_name__ = "PisakPageFlip"

    __gproperties__ =  {
        "target": (PagerWidget.__gtype__, "", "", GObject.PARAM_READWRITE),
    }

    def __init__(self):
        self._target = None
        super().__init__()

    @property
    def target(self):
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
                                    lambda *_: self._target.scan_page(), None)
        else:
            _LOG.warning("PageFlip without target: " + self.get_id())
