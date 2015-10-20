"""
Classes for defining scanning in JSON layouts
"""
import time

from gi.repository import Clutter, GObject

import pisak
from pisak import logger, exceptions, properties, configurator, dirs


_LOG = logger.get_logger(__name__)


class Scannable(object):
    """
    Interface of object scannable by switcher groups. Switcher groups expect
    widgets implement this interface.
    """
    def activate(self):
        """
        Performs widgets action.
        """
        raise NotImplementedError()

    def enable_hilite(self):
        """
        Enables hilite style for this widget.
        """
        raise NotImplementedError()

    def disable_hilite(self):
        """
        Disables hilite style for this widget.
        """
        raise NotImplementedError()

    def enable_scanned(self):
        """
        Enables scanned style for this widget.
        """
        raise NotImplementedError()

    def enable_lag_hilite(self):
        """
        Enables lag_hilite style for this widget.
        """
        raise NotImplementedError()

    def disable_lag_hilite(self):
        """
        Disables lag_hilite style for this widget.
        """
        raise NotImplementedError()

    def disable_scanned(self):
        """
        Enables hilite style for this widget.
        """
        raise NotImplementedError()

    def is_disabled(self):
        """
        Checks whether element is disabled from activation.
        """
        raise NotImplementedError()


class StylableScannable(Scannable):
    """
    Partial implementation of Scannable interface for stylable widgets.
    Hilighted and scanned widgets are marked with CSS pseudoclasses.
    """
    def enable_hilite(self):
        self.style_pseudo_class_add("hover")

    def disable_hilite(self):
        self.style_pseudo_class_remove("hover")

    def enable_scanned(self):
        self.style_pseudo_class_add("scanning")

    def disable_scanned(self):
        self.style_pseudo_class_remove("scanning")

    def enable_lag_hilite(self):
        self.style_pseudo_class_add("lag_hilite")
        
    def disable_lag_hilite(self):
        self.style_pseudo_class_remove("lag_hilite")

    def activate(self):
        """
        Performs widgets action.
        """
        raise NotImplementedError()

    def is_disabled(self):
        """
        Checks whether element is disabled from activation.
        """
        raise NotImplementedError()


class Strategy(Clutter.Actor):
    """
    Abstract base class for scanning strategies.
    """

    def __init__(self):
        super().__init__()
        self._group = None

    @property
    def group(self):
        """
        Reference to a group which owns the strategy.
        """
        return self._group

    @group.setter
    def group(self, value):
        self._group = value

    def select(self, element=None):
        """
        Selects currently highlighted element.
        """
        select_lag_disabled = False
        element = element or self.get_current_element()
        if element is None:
            _LOG.debug("There is no current element that could be frozen.")
            return
        self.play_selection_sound()
        if isinstance(element, Group):
            if not self.group.paused:
                self.group.stop_cycle()
                if self.select_lag > 0:
                    self._on_lag("select", element, self.select_lag)
                else:
                    self._do_select(element)
        elif hasattr(element, "enable_hilite"):
            pisak.app.window.pending_group = self.unwind_to
            if hasattr(element, "scanning_pauser") and element.scanning_pauser:
                if self.group.paused:
                    select_lag_disabled = True
                self.group.paused = not self.group.paused
            if not self.group.paused:
                self.group.stop_cycle()
            if self.select_lag > 0 and not select_lag_disabled:
                self._on_lag("select", element, self.select_lag)
            else:
                self._do_select(element)

    def _do_select(self, element):
        if isinstance(element, Group):
            if not self.group.killed:
                element.parent_group = self.group
                element.start_cycle()
        elif hasattr(element, "enable_hilite"):
            if not self.group.killed:
                element.activate()
            if hasattr(element, "disable_lag_hilite"):
                element.disable_lag_hilite()
            if not self.group.killed and not self.group.paused:
                # launch next group
                if pisak.app.window.pending_group:
                    pisak.app.window.pending_group.start_cycle()
                else:
                    self.group.start_cycle()
        else:
            raise Exception("Unsupported selection")

    def unwind(self):
        if self.unwind_to is not None:
            self.group.stop_cycle()
            self.unwind_to.start_cycle()
        else:
            self.group.stop_cycle()
            self.group.parent_group.start_cycle()

    def get_current_element(self):
        """
        Abstract method to extract currently highlighted element from an
        internal strategy state.

        :returns: currently highlighed element
        """
        raise NotImplementedError("Incomplete strategy implementation")


class ScanningException(exceptions.PisakException):
    pass


class _GroupObserver(object):
    """
    Helper class for Group. This class observes all group descendants. When
    subgroup change it schedules update in scanning seqence.
    """
    def __init__(self, group):
        self.group = group
        self._init_connections()

    def _observe(self, actor):
        """
        Adds handler recursively.
        """
        add_handler = actor.connect("actor-added", self._add_actor)
        remove_handler = actor.connect("actor-removed", self._remove_actor)
        for child in actor.get_children():
            self._observe(child)

    def _init_connections(self):
        # observe group children
        self._observe(self.group)

    def _add_actor(self, _parent, descendant):
        if isinstance(descendant, Group):
            # rescan: a new group was added
            self.group.schedule_update()
        elif hasattr(descendant, "enable_hilite"):
            # rescan: a new scannable was added
            self.group.schedule_update()
        else:
            # connect handler to a new actor
            for child in descendant.get_children():
                self._add_actor(descendant, child)
            self._observe(descendant)

    def _remove_actor(self, _parent, descendant):
        if isinstance(descendant, Group):
            # rescan: a group was removed
            self.group.schedule_update()
        elif hasattr(descendant, "enable_hilite"):
            # rescan: a scannable was removed
            self.group.schedule_update()
        else:
            for child in descendant.get_children():
                self._remove_actor(descendant, child)


class Group(Clutter.Actor, properties.PropertyAdapter,
            configurator.Configurable):
    """
    Container for grouping widgets for scanning purposes.
    """
    __gtype_name__ = "PisakScanningGroup"

    __gproperties__ = {
        "strategy": (
            Strategy.__gtype__,
            "", "",
            GObject.PARAM_READWRITE),
        "scanning-hilite": (
            GObject.TYPE_BOOLEAN,
            "", "", False,
            GObject.PARAM_READWRITE),
        "sound": (
            GObject.TYPE_STRING,
            "", "", "scan",
            GObject.PARAM_READWRITE
        )
    }

    def __init__(self):
        self.fresh_subgroups = False
        self._subgroups = []
        self._hilited = []
        self._scanned = []
        self._lag_hilited = []
        self._strategy = None
        self.sound = 'scan'
        self.paused = False
        self.killed = False
        self.suppress_collapse_select_on_init = False
        self.parent_group = None
        self.signal_source = None
        self._scanning_hilite = False
        self.user_action_handler = None
        self.input_handler_token = None
        super().__init__()
        self.observer = _GroupObserver(self)
        self.set_layout_manager(Clutter.BinLayout())
        self.apply_props()

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, value):
        if self.strategy is not None:
            self.strategy.group = None
        self._strategy = value
        if self.strategy is not None:
            self.strategy.group = self

    @property
    def scanning_hilite(self):
        return self._scanning_hilite

    @scanning_hilite.setter
    def scanning_hilite(self, value):
        self._scanning_hilite = value
        if not value:
            self.disable_scan_hilite()

    @property
    def sound(self):
        return self._sound

    @sound.setter
    def sound(self, name):
        if name:
            self._sound = self.get_sound(name)

    @staticmethod
    def get_sound(name):
        if name:
            return dirs.get_sound_path(name + '.wav')

    def schedule_update(self):
        self.fresh_subgroups = False

    def get_subgroups(self):
        if not self.fresh_subgroups:
            self.fresh_subgroups = True
            self._subgroups = list(self._gen_subgroups())
        return self._subgroups

    def _gen_subgroups(self):
        """
        Generator of all subgroups of the group.
        """
        to_scan = self.get_children()
        while len(to_scan) > 0:
            current = to_scan.pop(0)
            if isinstance(current, Group):
                if current.is_empty():
                    pass
                elif current.is_singular():
                    yield current.get_subgroups()[0]
                else:
                    yield current
            elif hasattr(current, "enable_hilite"):
                if not current.is_disabled():
                    yield current
                else:
                    pass
            else:
                to_scan.extend(current.get_children())

    def is_flat(self):
        """
        Test if group is flat, that is whether it contains
        any nested subgroups.

        :return: True if group has no subgroups, False otherwise.
        """
        for obj in self.get_children():
            if isinstance(obj, Group):
                return False
        return True

    def is_empty(self):
        """
        Tests if group is empty.
        :return: True if group has subgroups, False otherwise.
        """
        return len(self.get_subgroups()) == 0

    def is_singular(self):
        """
        Test if group has exactly 1 element.
        :return: True if group has exactly 1 subgroup, False otherwise.
        """
        return len(self.get_subgroups()) == 1

    def go_standby(self):
        """
        Turn off the scanning of the group and make it wait for being restarted
        by a user action.
        """
        if self.scanning_hilite:
            self.disable_scan_hilite()
        self.strategy.stop()
        self.user_action_handler = self.restart_cycle

    def restart_cycle(self):
        """
        Restart group cycle that had already been startd before but went
        standby in a meantime.
        """
        if self.input_handler_token is not None:
            self.signal_source.disconnect(self.input_handler_token)
        self.start_cycle()

    def start_cycle(self):
        """
        Starts group cycle. The cycle can be stopped with `stop_cycle` method.
        The cycle will also be stopped if the strategy's `has_next` method returns
        False.
        """
        _LOG.debug("Starting group {}".format(self.get_id()))
        self.observer = _GroupObserver(self)
        if not self.get_property("mapped"):
            self.connect('notify::mapped', lambda *_: self.start_cycle())
            message = \
                "Started cycle in unmapped group: {}".format(self.get_id())
            _LOG.warning(message)
            # TODO: do something wise here
            return

        _LOG.debug("Starting group {}".format(self.get_id()))

        collapsed = get_top_level_group([self])
        if collapsed is not self:
            collapsed.start_cycle()
            return

        if self.is_singular() and self._on_singular():
            return

        signal, handler, self.signal_source = \
            pisak.app.window.input_group.get_scanning_desc(self)
        self.input_handler_token = self.signal_source.connect(
            signal, lambda *args: handler(self, *args))
        self.killed = False
        if self.scanning_hilite:
            self.enable_scan_hilite()
        self.user_action_handler = self.strategy.select
        self.set_key_focus()
        self.strategy.start()

    def _on_singular(self):
        """
        Do something when the group is singular.
        """
        sub_element = self.get_subgroups()[0]
        if isinstance(sub_element, Group):
            msg = 'Group {} is singular. Starting its only subgroup.'
            _LOG.debug(msg.format(self.get_id()))
            sub_element.start_cycle()
            ret = True
        else:
            if not self.suppress_collapse_select_on_init:
                self.strategy.select(sub_element)
                ret = True
            else:
                self.suppress_collapse_select_on_init = False
                ret = False
        return ret

    def stop_cycle(self):
        """
        Stop currently running group cycle
        """
        if self.signal_source and self.input_handler_token:
            self.signal_source.disconnect(self.input_handler_token)
        if self.scanning_hilite:
            self.disable_scan_hilite()
        self.strategy.stop()

    def set_key_focus(self):
        stage = self.get_stage()
        if stage is not None:
            stage.set_key_focus(self)

    def key_release(self, _source, event):
        if event.unicode_value == ' ':
            self.user_action_handler()
        return True

    def button_release(self, source, event=None):
        self.user_action_handler()
        return False

    def _recursive_apply(self, test, operation):
        subgroups = self.get_subgroups()
        for s in subgroups:
            if test(s):
                operation(s)
            elif isinstance(s, Group):
                s._recursive_apply(test, operation)

    def enable_hilite(self):
        def operation(s):
            s.enable_hilite()
            self._hilited.append(s)
        self._recursive_apply(
            lambda s: hasattr(s, "enable_hilite"),
            operation)

    def disable_hilite(self):
        for s in self._hilited:
            s.disable_hilite()
        self._hilited = []

    def enable_lag_hilite(self):
        def operation(s):
            s.enable_lag_hilite()
            self._lag_hilited.append(s)
        self._recursive_apply(
            lambda s: hasattr(s, "enable_lag_hilite"),
            operation)

    def disable_lag_hilite(self):
        for s in self._lag_hilited:
            s.disable_lag_hilite()
        self._lag_hilited = []

    def enable_scan_hilite(self):
        def operation(s):
            s.enable_scanned()
            self._scanned.append(s)
        self._recursive_apply(
            lambda s: hasattr(s, "enable_scanned"),
            operation)

    def disable_scan_hilite(self):
        for s in self._scanned:
            s.disable_scanned()
        self._scanned = []


class BaseStrategy(Strategy, properties.PropertyAdapter,
                   configurator.Configurable):
    __gproperties__ = {
        "interval": (
            GObject.TYPE_UINT,
            "", "",
            0, GObject.G_MAXUINT, 1000,
            GObject.PARAM_READWRITE),
        "max-cycle-count": (
            GObject.TYPE_INT,
            "", "",
            -1, GObject.G_MAXINT, 2,
            GObject.PARAM_READWRITE),
        "unwind-to": (
            Group.__gtype__,
            "", "",
            GObject.PARAM_READWRITE),
        "start-up-lag": (
            GObject.TYPE_UINT,
            "", "",
            0, GObject.G_MAXUINT, 0,
            GObject.PARAM_READWRITE),
        "lag-hilite-mode": (
            GObject.TYPE_STRING,
            "", "", "",
            GObject.PARAM_READWRITE),
        "select-lag": (
            GObject.TYPE_UINT,
            "", "",
            0, GObject.G_MAXUINT, 0,
            GObject.PARAM_READWRITE)
        }

    def __init__(self):
        self._group = None
        self._allocation_slot = None
        self._subgroups = []
        self.index = None
        super().__init__()
        self._select_lag = 1000
        self._start_up_lag = 0
        self._interval = 1000
        self._lag_hilite_mode = "blink"
        self.blinking_freq = 100
        self._max_cycle_count = 2
        self._buttons = []
        self._unwind_to = None
        self.timeout_token = None
        self.player = pisak.app.sound_effects_player
        self.sound_support_enabled = pisak.config.as_bool("sound_support_enabled") and \
                             pisak.config.as_bool("sound_effects_enabled")
        self.apply_props()

    @property
    def start_up_lag(self):
        """
        Starting delay.
        """
        return self._start_up_lag

    @start_up_lag.setter
    def start_up_lag(self, value):
        self._start_up_lag = int(value)

    @property
    def lag_hilite_mode(self):
        """
        Type of starting lag hilite. Available are 'blink'
        and 'still'.
        """
        return self._lag_hilite_mode

    @lag_hilite_mode.setter
    def lag_hilite_mode(self, value):
        self._lag_hilite_mode = value

    @property
    def select_lag(self):
        """
        Duration of lag on selection.
        """
        return self._select_lag

    @select_lag.setter
    def select_lag(self, value):
        self._select_lag = int(value)

    @property
    def interval(self):
        """
        Scanning interval
        """
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = int(value)

    @property
    def max_cycle_count(self):
        """
        Number of repeats
        """
        return self._max_cycle_count

    @max_cycle_count.setter
    def max_cycle_count(self, value):
        self._max_cycle_count = int(value)

    @property
    def unwind_to(self):
        """
        Identifier of group which will be started after current group finishes
        """
        return self._unwind_to

    @unwind_to.setter
    def unwind_to(self, value):
        self._unwind_to = value

    def start(self):
        """
        Method invoked by a group which wants its scanning cycle
        to be started.
        """
        self.compute_sequence()
        if len(self._subgroups) == 0:
            # stop immediately
            self.index = None
            Clutter.threads_add_timeout(0, self.interval, self.cycle_timeout,
                                        self.timeout_token)
        else:
            if self.start_up_lag > 0:
                self._on_lag("start_up", self.group, self.start_up_lag)
            else:
                self._do_start()

    def _on_lag(self, lag_type, element_to_hilite, lag_duration):
        """
        Stops ('lags') the scanning proccess for the given amount of time
        and performs all the previously ordered actions, i.e. highlights
        the current element. In the end schedules an adequate closure.

        :param lag_type: type of lag to be performed. Currently there are
        only two of them: 'start_up' that can happen before the scanning
        process starts and 'select', after selection of an element.
        :param element_to_hilite: element that has scanning focus during the
        lag and that should be highlighted.
        :param lag_duration: duration of the lag in miliseconds.
        """
        if self.lag_hilite_mode == "blink":
            timeout_start = time.time()
            self.blink(element_to_hilite, timeout_start, lag_duration, 
                       self.blinking_freq)
        elif self.lag_hilite_mode == "still":
            if hasattr(element_to_hilite, "enable_lag_hilite"):
                element_to_hilite.enable_lag_hilite()
        if lag_type == "start_up":
            closure = self._do_start
            param = None
        elif lag_type == "select":
            closure = self._do_select
            param = element_to_hilite
        Clutter.threads_add_timeout(0, lag_duration, closure, param)

    @staticmethod
    def blink(blinking_element, timeout_start, overall_duration, freq):
        hilitten = False

        def switch_hilite():
            nonlocal hilitten

            when_to_exit = timeout_start + (overall_duration
                                            - 2*freq)/1000
            if time.time() > when_to_exit:
                if hasattr(blinking_element, "disable_lag_hilite"):
                    blinking_element.disable_lag_hilite()
                return False
            else:
                if hilitten:
                    if hasattr(blinking_element, "disable_lag_hilite"):
                        blinking_element.disable_lag_hilite()
                        hilitten = False
                else:
                    if hasattr(blinking_element, "enable_lag_hilite"):
                        blinking_element.enable_lag_hilite()
                        hilitten = True
                return True
        Clutter.threads_add_timeout(0, freq, switch_hilite)

    def stop(self):
        self.timeout_token = None
        self._stop_cycle()

    def _do_start(self, *_source):
        self.index = None
        self._cycle_count = 0
        self._expose_next(enforced=True)
        self.timeout_token = object()
        if hasattr(self.group, "disable_lag_hilite"):
            self.group.disable_lag_hilite()
        Clutter.threads_add_timeout(0, self.interval, self.cycle_timeout,
                                    self.timeout_token)

    def _stop_cycle(self):
        if self.index is not None:
            if self.index < len(self._subgroups):
                selection = self._subgroups[self.index]
                if hasattr(selection, "disable_hilite"):
                    selection.disable_hilite()
                elif isinstance(selection, Group):
                    selection.disable_hilite()
            self.index = None

    def _expose_next(self, enforced=False):
        # disable old hilite and increase index
        if self.index is not None and self.index < len(self._subgroups):
            selection = self._subgroups[self.index]
            if hasattr(selection, "disable_hilite"):
                selection.disable_hilite()
            elif isinstance(selection, Group):
                selection.disable_hilite()
            self.index = (self.index + 1) % len(self._subgroups)
        else:
            if not enforced:
                self.index = 0

        # check freshness
        if not self.group.fresh_subgroups:
            self.compute_sequence()
            # return to start when index is invalid
            if self.index is not None and self.index > len(self._subgroups):
                self.index = 0

        if self.index is not None and self.index < len(self._subgroups):
            selection = self._subgroups[self.index]
            if self.sound_support_enabled:
                if isinstance(selection, pisak.widgets.Button):
                    label = selection.get_label()
                    if label in selection.sounds:
                        self.player.play(selection.sounds[label])
                    elif label in [' ', '']:
                        icon_name = selection.current_icon_name
                        self.player.play(selection.sounds[icon_name])
                elif isinstance(selection, Group):
                    self.player.play(selection.sound)
                else:
                    self.play_scanning_sound()
            else:
                self.play_scanning_sound()
            if hasattr(selection, "enable_hilite"):
                selection.enable_hilite()
            elif isinstance(selection, Group):
                selection.enable_hilite()
        if self.index == len(self._subgroups) - 1:
            self._cycle_count += 1

    def _has_next(self):
        if len(self._subgroups) == 0:
            return False
        else:
            return (self.max_cycle_count == -1) or \
                (self._cycle_count < self.max_cycle_count)

    def _has_unwind_to(self):
        """
        Test whether scanning has anywhere to unwind to.

        :return: True if scanning has anywhere to unwind to, False otherwise.
        """
        return self.unwind_to is not None

    def _is_killed(self):
        """
        Test whether scanning of the group has been killed by some
        external agent.
        """
        return self.group.killed

    def _go_to_sleep(self):
        self.group.go_standby()

    def cycle_timeout(self, token):
        if self.timeout_token != token:
            # timeout event not from current cycle
            return False
        elif self._is_killed():
            self.group.stop_cycle()
            return False
        elif self._has_next():
            if not self.group.paused:
                self._expose_next()
            return True
        elif not self._has_unwind_to():
            self._go_to_sleep()
            return False
        else:
            self.unwind()
            return False

    def get_current_element(self):
        if self.index is not None and self.index < len(self._subgroups):
            return self._subgroups[self.index]
        else:
            msg = "There is no current element being a subgroup of group {}."
            _LOG.warning(msg.format(self.group.get_id()))

    @staticmethod
    def play_scanning_sound():
        if pisak.app:
            pisak.app.play_sound_effect('scanning')

    @staticmethod
    def play_selection_sound():
        if pisak.app:
            pisak.app.play_sound_effect('selection')


class RowStrategy(BaseStrategy):
    __gtype_name__ = "PisakRowStrategy"

    def __init__(self):
        self._allocation_slot = None
        super().__init__()

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, value):
        if self.group is not None:
            message = "Group strategy reuse, old {}, new {}"
            _LOG.warning(message.format(self.group.get_id(), value.get_id()))
            _LOG.debug("new {}, old {}".format(self.group, value))
            self.group.disconnect(self._allocation_slot)
        self._group = value
        if self.group is not None:
            self._allocation_slot = \
                self.group.connect("allocation-changed", self.update_rows)

    def update_rows(self, *_args):
        _LOG.debug("Row layout allocation changed")
        if self.index is not None:
            if self.index < len(self._subgroups):
                selection = self._subgroups[self.index]
            if hasattr(selection, "disable_hilite"):
                selection.disable_hilite()
        self.compute_sequence()
        self.index = None

    def compute_sequence(self):
        subgroups = self.group.get_subgroups()
        key_function = lambda a: list(reversed(a.get_transformed_position()))
        subgroups.sort(key=key_function)
        self._subgroups = subgroups


class ArbitraryOrderStrategy(BaseStrategy):
    """
    Strategy with arbitrary order of scanning
    """
    __gtype_name__ = "PisakArbitraryOrderStrategy"

    __gproperties__ = {
        "subgroup-order":
            (GObject.TYPE_STRING, "", "", "", GObject.PARAM_READWRITE),
    }

    def __init__(self):
        self._subgroup_order = []
        super().__init__()

    @property
    def subgroup_order(self):
        """
        List of elements to scan
        """
        return self._subgroup_order

    @subgroup_order.setter
    def subgroup_order(self, value):
        value_list = [v.strip() for v in value.split(",")]
        self._subgroup_order = value_list

    def compute_sequence(self):
        subgroups = self.group.get_subgroups()
        unordered = dict([(s.get_id(), s) for s in subgroups])
        self._subgroups = []
        for s in self.subgroup_order:
            if s in unordered:
                self._subgroups.append(unordered[s])


def get_top_level_group(top_level):
    """
    Get a non-empty top-level scanning group from the given object tree.

    :param top_level: list of the top-level objects from the object tree.

    :return: top-level scanning group or None.
    """
    def get_collapsed(top_level_group):
        """
        Collapse the given top-level scanning group.
        If there is only one non-empty scanning group being
        a subgroup of the given top-level group then such a non-empty
        group is returned. Otherwise the given top-level group is returned.
        For the definition of a group being empty
        :see: `Group.is_empty`.

        :param top_level_group: scanning group that should get collapsed.

        :return: scanning group.
        """
        def is_empty_branch(node_list):
            """
            Check if the given branch is empty from the
            scanning point of view, that is whether there are any elements
            that could get scanned.

            :param node_list: list of top-level objects from some object branch.

            :return: True or False.
            """
            nested_nodes = []
            for node in node_list:
                if (isinstance(node, Group) and node.is_flat() and not
                        node.is_empty()):
                    return False
                else:
                    nested_nodes.extend(node.get_children())
            return is_empty_branch(nested_nodes) if nested_nodes else True

        branches = []

        def find_branches(origin_level):
            """
            Find all the scanning branches in the object tree, originating
            from the given top level.

            :param origin_level: list of top-level objects.

            :return: None.
            """
            for element in origin_level:
                if isinstance(element, Group):
                    branches.append(element)
                else:
                    find_branches(element.get_children())

        non_empty = None
        non_empty_count = 0
        find_branches(top_level_group.get_children())
        for branch in branches:
            branch_list = [branch]
            if not is_empty_branch(branch_list):
                non_empty = get_top_level_group(branch_list)
                non_empty_count += 1
        return non_empty if non_empty_count == 1 else top_level_group

    next_level = []
    for obj in top_level:
        if isinstance(obj, Group):
            return get_collapsed(obj)
        else:
            next_level.extend(obj.get_children())
    if next_level:
        return get_top_level_group(next_level)
