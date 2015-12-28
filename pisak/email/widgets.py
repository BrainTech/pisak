"""
Email application specific widgets.
"""
import datetime
from gi.repository import Clutter, Mx, Pango, GObject

import pisak
from pisak import logger, pager, widgets, layout, unit
from pisak.email import imap_client


_LOG = logger.get_logger(__name__)


DATE_FORMAT = '%d-%m-%Y %H:%M'

ERROR_MESSAGES = {
    "no_internet": "Brak połączenia z internetem.\nSprawdź "
                   "łącze i spróbuj ponownie",
    "login_fail": "Błąd podczas logowania. Sprawdź swoje ustawienia\n"
                    "skrzynki i spróbuj ponownie.",
    "empty_mailbox": "Brak wiadomości w skrzynce.",
    "invalid_sent_box_name": "Nieprawidłowa nazwa skrzynki wysłanych.",
    "invalid_email_address": "Podałeś błędny adres email.\n"
                "Adres powinien zawierać znak @ i kropkę w nazwie domeny.\n"
                "Na przykład:     JanKowalski@gmail.com",
    "message_send_fail": "Wysyłanie wiadomości nie powiodło się.\n"
                    "Sprawdź połączenie z internetem i spróbuj ponownie.",
    "invalid_credentials": "Nieprawidłowa nazwa użytkownika lub hasło.",
    "unknown": "Wystąpił błąd.\nSprawdź swoje połączenie internetowe \ni spróbuj ponownie.",
    'too-slow-connection': 'Błąd połączenia - \nzbyt wolne połączenie z internetem.'
}


class AddressTileSource(pager.DataSource):
    """
    Data source that provides tiles representing different addresses
    from the address book.
    """
    __gtype_name__ = 'PisakEmailAddressTileSource'

    def __init__(self):
        super().__init__()

    def _produce_item(self, contact):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        frame = widgets.Frame()
        frame.set_x_expand(False)
        frame.set_y_expand(False)
        frame.set_size(*tile.get_size())
        tile.add_frame(frame)
        tile.style_class = 'PisakEmailAddressTile'
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", self.item_handler, contact)
        tile.label_text = contact.content.name if contact.content.name \
            else contact.content.address
        if contact.content.photo:
            tile.preview_path = contact.content.photo
        tile.spec["toggled"] = contact.flags.get("picked")
        return tile


class MailboxTileSource(pager.DataSource):
    """
    Data source that provides tiles representing messages in various
    email mailboxes.
    """

    __gtype_name__ = 'PisakEmailMailboxTileSource'

    __gproperties__ = {
        'mailbox': (
            str, '', '', '', GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self._mailbox = None
        now = datetime.datetime.now()
        maxdelta = datetime.timedelta(10**4)
        self._data_sorting_key = lambda msg: ((now - msg["Date"]) if msg else maxdelta)

    @property
    def mailbox(self):
        """
        Name of the mailbox. Avalaible: 'inbox', 'sent_box'.
        """
        return self._mailbox

    @mailbox.setter
    def mailbox(self, value):
        self._mailbox = value

    def _produce_item(self, message_obj):
        message = message_obj.content
        tile = MailboxTile(self.mailbox)
        self._prepare_item(tile)
        tile.connect('clicked', self.item_handler, message_obj)

        for label, value in (
            ('from', message['From'][0] or message['From'][1]) if
                self._mailbox == 'inbox' else
            ('to', message['To'][0] or message['To'][1]),
            ('subject', message['Subject']),
            ('date', message['Date'].strftime(DATE_FORMAT))
        ):
            try:
                getattr(tile, label).set_text(value)
            except AttributeError as e:
                _LOG.warning(e)
        return tile

    def _query_portion_of_data(self, ids):
        imap_client = pisak.app.box["imap_client"]
        return imap_client.get_many_previews_from_inbox(ids) if \
            self._mailbox == 'inbox' else \
            imap_client.get_many_previews_from_sent_box(ids)

    def _query_ids(self):
        imap_client = pisak.app.box["imap_client"]
        return imap_client.get_inbox_ids() if \
            self._mailbox == 'inbox' else \
            imap_client.get_sent_box_ids()


class DraftsTileSource(pager.DataSource):
    """
    Data source that provides tiles representing messages in the drafts folder.
    """
    __gtype_name__ = 'PisakEmailDraftsTileSource'

    def __init__(self):
        super().__init__()
        imap_client = pisak.app.box["imap_client"]
        self._data_loader = imap_client.get_many_previews_from_sent_box
        self._ids_checker = imap_client.get_sent_box_ids
        self.lazy_loading = True

    def _produce_item(self, message):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.style_class = "PisakEmailDraftsTile"
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", self.item_handler, message)
        return tile


class MailboxTile(widgets.PhotoTile):
    """
    Email specific tile widget.
    """

    def __init__(self, mailbox):
        super().__init__()
        self.hilite_tool = widgets.Aperture()

        self.label = layout.Box()
        self.box.add_child(self.label)
        self.label.orientation = Clutter.Orientation.VERTICAL
        self.label.ratio_spacing = 0.03

        frame = widgets.Frame()
        frame.set_style_class('PisakEmailMessageTile')
        self.add_child(frame)

        margin = unit.h(0.0095)

        # create separate label for each header, specific to the given
        # `mailbox`; each label is set as an attribute of `self` with a
        # name of the corresponding header's lower-cased name;
        # list of headers is at the moment taken from the `imap_client` module.
        for header in imap_client.MAILBOX_HEADERS[mailbox]:
            label = widgets.Label()
            setattr(self, header.lower(), label)
            label.set_margin_right(margin)
            label.set_margin_left(margin)
            label.get_clutter_text().set_line_alignment(
                                Pango.Alignment.CENTER)
            label.set_style_class('PisakEmailMessageTile' + header)
            self.label.add_child(label)

        # set the get_text method to the topic label so it can be read
        self.label.get_text = self.label.get_children()[0].get_text


class EmailButton(widgets.Button):
    """
    Email application specific button.
    """
    __gtype_name__ = "PisakEmailButton"

    __gproperties__ = {
        "extra-label": (
            str, "", "", "",
            GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self._extra_label = None

    def set_extra_label(self, extra):
        """
        Set some extra label that will be concatenated to a default one.

        :param extra: text to be an extra label.
        """
        self.set_label(self.get_label() + extra)
        self._extra_label = extra

    def get_label(self):
        """
        Get label without any extra labels.

        :return: label, string.
        """
        if self._extra_label:
            label = self.clutter_text.get_text()
            return label[: label.rfind(self._extra_label)].strip()
        else:
            return super().get_label()
