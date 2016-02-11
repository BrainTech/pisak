import random
from time import time

from gi.repository import Clutter

from pisak import logger
from pisak.obci import ws_client


class elements_group(list):

    def id_for_obci(self):
        return 'Group: ' + ', '.join([element.id_for_obci() for element in self])


class Scanner:

    def __init__(self, content):
        self._ws_client = ws_client.Client(self._on_obci_feedback)
        self._rows = []
        self._columns = []
        self._elements = elements_group()
        self.update_content(content)

        self.interval = 100  # scanning interval in miliseconds
        self.flash_duration = 100  # duration of an item being flashed

        self._strategy = 'row'
        self._sampling = 'random-replacement'

        # step of the currently running scanning process:
        self._idx = 0

        self._greedy_coeff = 5

        self._groups = []  # custom groups

        self._current_scenario = None  # currently run scenario

        self._current_cycle_start = None  # when the current strategy cycle was started

        # list of currently scanned items (elements or some groups of elements):
        self._items = None
        # list of ids corresponding to the currently scanned items:
        self._sampling_pool = []
        # rule describing how to sample items, callable:
        self._sampling_rule = None

        self._working = False
        self._current_item = None  # can be an element or an elements_group instance
        self._logger = logger.get_obci_logger()

    @property
    def strategy(self):
        """
        Each strategy is described as a two-element tuple, available options:
            - row
            - column
            - element
            - row+column
            - custom

            - random-replacement
            - random-replacement-greedy
            - random-no-replacement
            - order
        """
        return (self._strategy, self._sampling)

    @strategy.setter
    def strategy(self, value):
        assert isinstance(value, tuple), 'strategy is a two-element tuple'
        self._strategy = value[0]
        self._sampling = value[1]

        if self._strategy == 'row':
            self._items = self._rows
        elif self._strategy == 'column':
            self._items = self._columns
        elif self._strategy == 'element':
            self._items = self._elements
        elif self._strategy == 'custom':
            self._items = self._groups
        elif self._strategy == 'row+column':
            self._items = self._rows + self._columns
        else:
            raise AttributeError('No such strategy available.')

        if self._sampling == 'order':
            def rule():
                return self._items[self._idx % len(self._items)]

            self._sampling_pool = list(range(len(self._items)))
            self._sampling_rule = rule
        elif self._sampling == 'random-replacement':
            def rule():
                return self._items[random.choice(self._sampling_pool)]

            self._sampling_pool = list(range(len(self._items)))
            self._sampling_rule = rule
        elif self._sampling == 'random-no-replacement':
            def rule():
                if not self._sampling_pool:
                    self._sampling_pool = list(range(len(self._items)))
                    random.shuffle(self._sampling_pool)
                return self._items[self._sampling_pool.pop()]

            self._sampling_pool = list(range(len(self._items)))
            random.shuffle(self._sampling_pool)
            self._sampling_rule = rule
        elif self._sampling == 'random-replacement-greedy':
            def rule():
                if not self._sampling_pool:
                    self._sampling_pool = list(range(len(self._items))) * self._greedy_coeff
                    random.shuffle(self._sampling_pool)
                return self._items[self._sampling_pool.pop()]

            self._sampling_pool = list(range(len(self._items))) * self._greedy_coeff
            random.shuffle(self._sampling_pool)
            self._sampling_rule = rule
        else:
            raise AttributeError('No such sampling in the strategy available.')

        self._reset_params()

    def start(self, duration=-1):
        self._working = True
        self._current_cycle_start = time()
        Clutter.threads_add_timeout(0, self.interval, self._on_cycle_timeout, duration)

    def stop(self):
        self._working = False

    def clean_up(self):
        self._logger.save()
        self._stop_obci()

    def run_scenario(self, scenario):
        """
        Run scanning scenario.

        :param scenario: list of tuples, each tuple consists of:
            - strategy - two-element tuple, see `strategy`;
            - duration - integer, number of miliseconds to run given strategy.
        """
        self._current_scenario = scenario
        self._start_obci()
        self._run_pending()

    def update_content(self, new_content):
        self._stop_obci()
        number_of_elements = self._parse_content(new_content)
        self._new_view_for_obci(number_of_elements)

    def _run_pending(self):
        if self._current_scenario:
            strategy, duration = self._current_scenario.pop(0)
            self.strategy = strategy
            self.start(duration/1000)
        else:
            self.clean_up()

    def _reset_params(self):
        self._idx = 0

    def _parse_content(self, content):
        idx = 0
        for box in content.get_children():
            new_row = elements_group()
            self._rows.append(new_row)
            for column_idx, element in enumerate(box.get_children()[0].get_children()):
                element.id_for_obci = lambda: str(idx)
                new_row.append(element)
                self._elements.append(element)
                if column_idx >= len(self._columns):
                    new_column = elements_group((element,))
                    self._columns.append(new_column)
                else:
                    self._columns[column_idx].append(element)
                idx += 1
        return len(self._elements)

    def _pick_next_item(self):
        self._current_item = self._sampling_rule()
        self._idx += 1

    def _flash_item_on(self, item):
        if isinstance(item, list):
            for sub_item in item:
                self._flash_item_on(sub_item)
        elif item:
                item.enable_hilite()

    def _flash_item_off(self, item):
        if isinstance(item, list):
            for sub_item in item:
                self._flash_item_off(sub_item)
        elif item:
                item.disable_hilite()

    def _do_transition(self):
        self._flash_item_off(self._current_item)
        self._pick_next_item()
        self._flash_item_on(self._current_item)

    def _format_event(self):
        return ' - '.join([str(time()), self._current_item.id_for_obci()])

    def _log_event(self):
        self._logger.log(self._format_event())

    def _report_event(self):
        self._send_msg_to_obci(self._format_event())

    def _on_cycle_timeout(self, duration):
        if 0 < duration < time() - self._current_cycle_start:
            self._flash_item_off(self._current_item)
            self.stop()
            self._run_pending()
            return False
        else:
            if self._working:
                self._do_transition()
                self._report_event()
                return True
            else:
                self._flash_item_off(self._current_item)
                return False

    def _on_obci_feedback(self, msg):
        msg = str(msg)
        Clutter.threads_add_timeout(0, 5, lambda *_: self._parse_obci_feedback(msg))

    def _parse_obci_feedback(self, msg):
        print(msg)
        if 'error' not in msg:
            self._on_obci_event(msg)
        else:
            self._on_obci_error(msg)

    def _on_obci_event(self, msg):
        pass

    def _on_obci_error(self, msg):
        pass

    def _start_obci(self):
        self._send_msg_to_obci('start')

    def _stop_obci(self):
        self._send_msg_to_obci('stop')

    def _new_view_for_obci(self, number_of_elements):
        self._send_msg_to_obci('new view, number of elements: ' +
                               str(number_of_elements))

    def _send_msg_to_obci(self, msg):
        self._ws_client.send(msg)


def parse_logs():
    path = logger.OBCI_LOGS_PATH
    with open(path, 'r') as file:
        lines = file.readlines()
    for line in lines:
        timestamp, event = line.split(' - ', maxsplit=1)
        event = event.rstrip('\n')
