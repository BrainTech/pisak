from time import time

from gi.repository import Clutter

from pisak import logger


class Scanner:

    def __init__(self, content):
        self._rows = []
        self._columns = []
        self._elements = []
        self._parse_content(content)

        self.interval = 100  # scanning interval in miliseconds
        self.flash_duration = 100  # duration of an item being flashed

        self._strategy = 'row'
        self._sampling = 'random-replacement'

        self._groups = []  # custom groups

        # list of currently scanned items (elements or some lists of elements):
        self._items = []
        # list of ids corresponding to the currently scanned items:
        self._sampling_pool = []
        # rule describing how to sample items, callable:
        self._sampling_rule = None

        self._working = False
        self._current_item = None
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

    def start(self):
        self._working = True

    def stop(self):
        self._working = False

    def clean_up(self):
        self._logger.save()

    def run_scenario(self, scenario):
        """
        Run scanning scenario.

        :param scenario: list of tuples, each tuple consists of:
            - strategy - two-element tuple, see `strategy`;
            - time - integer, number of miliseconds to run given strategy.
        """
        pass

    def _parse_content(self, content):
        pass

    def _pick_next_item(self):
        pass

    def _flash_current_item_on(self):
        pass

    def _flash_current_item_off(self):
        pass

    def _do_transition(self):
        self._flash_current_item_off()
        self._pick_next_item()
        self._flash_current_item_on()

    def _log_event(self):
        self._logger.log(time(), self._current_item.uid)

    def _on_cycle_timeout(self):
        if self._working:
            self._do_transition()
            self._log_event()
            return True
        else:
            return False