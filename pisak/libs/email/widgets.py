from gi.repository import Clutter, Mx, Pango, GObject

from pisak import logger
from pisak.libs import pager, widgets, layout, unit
from pisak.libs.email import imap_client


_LOG = logger.get_logger(__name__)


DATE_FORMAT = '%d-%m-%Y %H:%M'


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

    SPECIFIC_HEADER = {
        'inbox':lambda message:
            ('from', message['From'][0] or message['From'][1]),
        'sent_box': lambda message:
            ('to', message['To'][0] or message['To'][1])
    }

    def __init__(self):
        super().__init__()
        self._mailbox = None

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
            self.SPECIFIC_HEADER[self.mailbox](message),
            ('subject', message['Subject']),
            ('date', message['Date'].strftime(DATE_FORMAT))
        ):
            try:
                getattr(tile, label).set_text(value)
            except AttributeError as e:
                _LOG.warning(e)

        return tile


class DraftsTileSource(pager.DataSource):
    """
    Data source that provides tiles representing messages in the drafts folder.
    """
    __gtype_name__ = 'PisakEmailDraftsTileSource'

    def __init__(self):
        super().__init__()

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
            label = Mx.Label()
            setattr(self, header.lower(), label)
            label.set_margin_right(margin)
            label.set_margin_left(margin)
            label.get_clutter_text().set_line_alignment(
                                Pango.Alignment.CENTER)
            label.set_style_class('PisakEmailMessageTile' + header)
            self.label.add_child(label)


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

    @property
    def extra_label(self):
        """
        Extra label added to the default label with some extra
        spacing between. Type of the property is string.
        """
        return self._extra_label

    @extra_label.setter
    def extra_label(self, value):
        assert isinstance(value, str), "`extra_label` must be string"
        self._extra_label = value
        self._add_extra_label(value)

    def _add_extra_label(self, value):
        from_padd = 0.5
        from_avalaible = 0.3
        padding_width = self._padding.get_width() if self._padding else 0
        content_width  = \
            self.content_offset + padding_width + \
            self.image.get_width() + self.clutter_text.get_width() + \
            (self.space.get_width() if self.space else 0)
        avalaible_width = \
            self.get_width() - content_width + from_padd*padding_width
        if padding_width:
            self._padding.set_width((1 - from_padd) * padding_width)
        else:
            avalaible_width *= from_avalaible
        extra_space = Clutter.Text()
        max_iter = 100
        it = 0
        while extra_space.get_width() < avalaible_width and it < max_iter:
            extra_space.set_text(extra_space.get_text() + " ")
            it += 1
        self.clutter_text.set_text(
            value + extra_space.get_text() + self.clutter_text.get_text())
