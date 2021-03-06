import urllib
import socket
import textwrap

from gi.repository import GObject, Pango

from pisak import res, logger, exceptions, handlers
from pisak.viewer import model
from pisak.email import address_book, message, imap_client, config, widgets

import pisak.email.handlers  # @UnusedImport
import pisak.speller.handlers  # @UnusedImport
import pisak.speller.widgets  # @UnusedImport
import pisak.viewer.widgets  # @UnusedImport


_LOG = logger.get_logger(__name__)


REQUEST_TIMEOUT = 5  # web request duration limit in seconds


MESSAGES = widgets.ERROR_MESSAGES


ELEMENTS = {
    "new_message": message.SimpleMessage(),
    "address_book": address_book.AddressBook(),
    "imap_client": imap_client.IMAPClient()
}


VIEWS_MAP = {
    "new_message_initial_view": "email/speller_message_subject"
}


BUILTIN_CONTACTS = [
    {
        "name": "PISAK",
        "address": "kontakt@pisak.org",
        "photo": res.get("logo_pisak.png")
    }
]

def internet_on():
    try:
        response = urllib.request.urlopen('http://216.58.209.67',timeout=1)
        return True
    except urllib.error.URLError as err:
        return False

def prepare_main_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_inbox", "email/inbox")
    handlers.button_to_view(window, script, "button_sent", "email/sent")
    handlers.button_to_view(window, script, "button_drafts", "email/drafts")
    handlers.button_to_view(
        window, script, "button_address_book", "email/address_book")
    handlers.button_to_view(window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])

    for contact in BUILTIN_CONTACTS:
        try:
            app.box["address_book"].add_contact(contact)
        except address_book.AddressBookError:
            pass  # TODO: notify the user

    counter_label = '  ( {} )'

    try:
        contact_count = app.box["address_book"].get_count()
        window.ui.button_address_book.set_extra_label(
            counter_label.format(str(contact_count))
        )
    except address_book.AddressBookError:
        pass  # TODO: say something

    if not(internet_on()):
        window.load_popup(MESSAGES["no_internet"], 'main_panel/main')
        return False
    
    client = app.box["imap_client"]
    oblig_keys =  {key:client._setup[key] for key in client._setup if key!='sent_folder'}
    if ( any(bool(value) == False for value in oblig_keys.values()) ):
            window.load_popup(MESSAGES["empty_config"], 'main_panel/main')
            return False
    try:
        try:
            client.login()
        except imap_client.InvalidCredentialsError:
            window.load_popup(MESSAGES["invalid_credentials"], app.main_quit)
            return False
        except imap_client.IMAPClientError:
            window.load_popup(MESSAGES["login_fail"], app.main_quit)
            return False
        else:
            try:
                inbox_all, inbox_unseen = client.get_inbox_status()
                window.ui.button_inbox.set_extra_label(
                    counter_label.format("  /  ".join([str(inbox_unseen),
                                                       str(inbox_all)]))
                )
            except imap_client.IMAPClientError:
                return False # TODO: do something
            
            try:
                sent_box_count = client.get_sent_box_count()
                window.ui.button_sent.set_extra_label(
                    counter_label.format(str(sent_box_count))
                )
            except imap_client.IMAPClientError:
                return False # TODO: display some warning

    except socket.timeout:
        window.load_popup(MESSAGES["too-slow-connection"], app.main_quit)
        return False
    except exceptions.PisakException:
        window.load_popup(MESSAGES["unknown"], app.main_quit)
        return False
            
def prepare_drafts_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")


def prepare_inbox_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")

    client = app.box["imap_client"]

    data_source = script.get_object("data_source")

    def load_single_msg(_tile, message_preview):
        window.load_view(
            "email/single_message",
            {
                "message_uid": message_preview.content["UID"],
                "message_source": client.get_message_from_inbox,
                'msg_ids_list': data_source.get_data_ids_list(),
                "previous_view": 'inbox'
            }
        )

    data_source.item_handler = load_single_msg

    try:
        inbox_count, _inbox_unseen = client.get_inbox_status()
    except socket.timeout:
        window.load_popup(MESSAGES["too-slow-connection"], app.main_quit)
    except imap_client.IMAPClientError:
        window.load_popup(MESSAGES["unknown"],
                          container=window.ui.pager)
    except exceptions.NoInternetError:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.pager)
    else:
        if inbox_count == 0:
            window.load_popup(MESSAGES["empty_mailbox"],
                              container=window.ui.pager)
        else:
            data_source.lazy_loading = True


def prepare_sent_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")

    client = app.box["imap_client"]

    data_source = script.get_object("data_source")

    def load_single_msg(_tile, message_preview):
        window.load_view(
            "email/single_message",
            {
                "message_uid": message_preview.content["UID"],
                "message_source": client.get_message_from_sent_box,
                'msg_ids_list': data_source.get_data_ids_list(),
                "previous_view": "sent"
            }
        )

    data_source.item_handler = load_single_msg
        
    try:
        sent_box_count = client.get_sent_box_count()
    except socket.timeout:
        window.load_popup(MESSAGES["too-slow-connection"], app.main_quit)
    except imap_client.IMAPClientError:
        window.load_popup(MESSAGES["invalid_sent_box_name"],
                          container=window.ui.pager)
    except exceptions.NoInternetError:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.pager)
    else:
        if sent_box_count == 0:
            window.load_popup(MESSAGES["empty_mailbox"],
                              container=window.ui.pager)
        else:
            data_source.lazy_loading = True


def prepare_speller_message_body_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    if data and 'original_msg' in data and data['original_msg'].get('Body'):
        body = '\n' + textwrap.indent(
            data['original_msg']['Body'], '>', lambda line: True)
        window.ui.text_box.type_text(body)
        window.ui.text_box.set_cursor_position(0)
    elif app.box['new_message'].body:
        window.ui.text_box.type_text(app.box['new_message'].body)
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed",
                        "email/address_book", {"pick_recipients_mode": True})


def prepare_speller_message_subject_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    if data and 'original_msg' in data:
        subject = data['original_msg']['Subject']
        action = data.get('action')
        if action == 'forward':
            pre = 'PD: '
        elif action in ('reply', 'reply_all'):
            pre = 'Odp: '
        else:
            pre = ''

        window.ui.text_box.type_text(pre + subject)
    elif app.box['new_message'].subject:
        window.ui.text_box.type_text(app.box['new_message'].subject)

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed",
                            "email/speller_message_body", data)


def prepare_speller_message_to_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed", "email/sent")


def prepare_address_book_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    data_source = script.get_object("data_source")

    contacts = []
    try:
        contacts = app.box["address_book"].get_all_contacts()
    except address_book.AddressBookError:
        pass  # TODO: display warning and/or try to reload the view

    def on_contact_select(tile, contact):
        """
        On contact tile select.

        :param tile: tile representing single contact
        :param contact: contact dictionary
        """
        tile.toggled = contact.flags["picked"] = \
            not  contact.flags["picked"] if "picked" in \
            contact.flags else True
        if tile.toggled:
            app.box["new_message"].recipients = contact.content.address
        else:
            app.box["new_message"].remove_recipient(contact.content.address)

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/main")

    if data and data.get("pick_recipients_mode"):
        specific_button= window.ui.button_send_message
        tile_handler = lambda tile, contact: on_contact_select(tile, contact)
        handlers.button_to_view(window, script,
                                "button_send_message", "email/sent")
    else:
        specific_button = window.ui.button_new_contact
        tile_handler = lambda tile, contact: window.load_view(
            "email/contact", {"contact_id": contact.content.id})
        handlers.button_to_view(
            window, script, "button_new_contact",
            "email/speller_contact_address")

    window.ui.button_menu_box.replace_child(
        window.ui.button_specific, specific_button)
    data_source.item_handler = tile_handler

    # set 'picked' flag of a given contact to True if the view is in the
    # 'pick recipients' mode and the contact's email address has already been
    # on the new message recipients list.
    data_source.data = sorted(data_source.produce_data(
        [
            (
                contact,
                {'picked': True} if
                (data and data.get("pick_recipients_mode")) and
                contact.address in app.box["new_message"].recipients else
                None
            ) for contact in contacts
        ],
        lambda contact: contact.name if contact.name else
                        contact.address)
    )


def prepare_contact_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/main")

    if data:
        try:
            contact = app.box["address_book"].get_contact(data["contact_id"])
        except address_book.AddressBookError:
            contact = None  # TODO: display warning
        if contact:
            window.ui.contact_address_text.set_text(contact.address)
            if contact.name:
                window.ui.contact_name_text.set_text(contact.name)
            if contact.photo:
                try:
                    window.ui.photo.set_from_file(contact.photo)
                except GObject.GError as e:
                    _LOG.error(e)

            def add_recipient():
                app.box["new_message"].recipients = contact.address

            handlers.connect_button(
                script, "button_create_message", add_recipient)
            handlers.button_to_view(
                window, script, "button_create_message",
                "email/speller_message_subject")
            handlers.button_to_view(
                window, script, "button_edit_name",
                "email/speller_contact_name",
                {"contact_id": contact.id, "contact_name": contact.name})
            handlers.button_to_view(
                window, script, "button_edit_address",
                "email/speller_contact_address",
                {"contact_id": contact.id,
                 "contact_address": contact.address})
            handlers.button_to_view(
                window, script, "button_edit_photo",
                "email/viewer_contact_library",
                {"contact_id": contact.id, "contact_photo": contact.photo})


def prepare_speller_contact_name_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    def edit_contact_name():
        try:
            app.box["address_book"].edit_contact_name(
                data["contact_id"], window.ui.text_box.get_text())
        except address_book.AddressBookError:
            pass  # TODO: display warning

    handlers.button_to_view(window, script, "button_exit")
    handlers.connect_button(script, "button_proceed", edit_contact_name)
    handlers.button_to_view(window, script, "button_proceed", "email/contact",
                            {"contact_id": data["contact_id"]})

    if data.get("contact_name"):
        window.ui.text_box.type_text(data["contact_name"])


def prepare_speller_contact_address_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    text_box = window.ui.text_box

    if not data or (data and data.get("new")):
        def create_contact():
            address = text_box.get_text()
            if address:
                try:
                    resp = app.box["address_book"].add_contact(
                        {"address": address})
                    if not resp:
                        # TODO: say that address is not unique
                        pass
                    contact = app.box["address_book"].get_contact_by_address(
                        address)
                    load = ("email/speller_contact_name",
                            {"contact_id": contact.id})
                except address_book.AddressBookError:
                    # TODO: notify about failure
                    load = ("email/address_book",)
            else:
                load = ("email/address_book",)

            window.load_view(*load)

        button_proceed_handler = create_contact
    else:
        if data.get("contact_address"):
            text_box.type_text(data["contact_address"])

        def edit_contact_address():
            try:
                app.box["address_book"].edit_contact_address(
                    data["contact_id"], text_box.get_text())
            except address_book.AddressBookError:
                pass  # TODO: display warning

            window.load_view("email/contact",
                             {"contact_id": data["contact_id"]})

        button_proceed_handler = edit_contact_address

    handlers.button_to_view(window, script, "button_exit")
    handlers.connect_button(script, "button_proceed", button_proceed_handler)


def prepare_viewer_contact_library_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/contact",
                            {"contact_id": data["contact_id"]})

    tile_source = script.get_object("library_data")
    tile_source.item_handler = lambda tile, album: window.load_view(
        "email/viewer_contact_album",
        {"album_id": album, "contact_id": data["contact_id"]})


def prepare_viewer_contact_album_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    contact_id = data["contact_id"]

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_library", "email/viewer_contact_library",
        {"contact_id": contact_id})

    album_id = data["album_id"]
    library = model.get_library()
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)
    data_source = script.get_object("album_data")

    def photo_tile_handler(tile, photo_id, album_id):
        try:
            app.box["address_book"].edit_contact_photo(
                contact_id, library.get_item_by_id(photo_id).path)
        except address_book.AddressBookError:
            pass  # TODO: display warning
        window.load_view("email/contact", {"contact_id": contact_id})

    data_source.item_handler = photo_tile_handler
    data_source.data_set_idx = album_id


def prepare_single_message_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    box = data["previous_view"]
    msg_id = data["message_uid"]

    def remove_message():
        try:
            if box == 'sent':
                app.box['imap_client'].delete_message_from_sent_box(msg_id)
            elif box == 'inbox':
                app.box['imap_client'].delete_message_from_inbox(msg_id)
        except socket.timeout:
            window.load_popup(MESSAGES["too-slow-connection"], app.main_quit)

        window.load_view('email/{}'.format(box))

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script,
                            "button_back", "email/{}".format(box))
    handlers.connect_button(script, "button_remove", remove_message)
    handlers.button_to_view(window, script, "button_new_mail",
                            VIEWS_MAP["new_message_initial_view"])

    try:
        message = data["message_source"](data["message_uid"])
    except socket.timeout:
        window.load_popup(MESSAGES["too-slow-connection"], app.main_quit)
    except imap_client.IMAPClientError:
        window.load_popup(MESSAGES["unknown"],
                          container=window.ui.message_content)
    except exceptions.NoInternetError:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.message_content)
    else:
        window.ui.message_subject.set_text(message["Subject"])
        window.ui.from_content.set_text(
            "; ".join([record[0] + " <" + record[1] + ">" for
                       record in message["From"]]))
        window.ui.to_content.set_text(
            "; ".join([record[0] + " <" + record[1] + ">" for
                       record in message["To"]]))
        window.ui.date_content.set_text(str(message["Date"]))

        if "Body" in message:
            window.ui.message_body.type_text(message["Body"])
            window.ui.message_body.set_cursor_position(0)
            window.ui.message_body._fix_scroll()

        def reply():
            """
            Send a reply only to the sender of the original message.
            """
            # pick emal address only of the main sender from the
            # list of headers:
            app.box['new_message'].recipients = message['From'][0][1]
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'reply'})

        def reply_all():
            """
            Send a reply to the sender and all the recipients
            of the original message.
            """
            # pick email addresses of the main sender and of all
            # the recipients except myself:
            setup = config.Config().get_account_setup()
            app.box['new_message'].recipients = \
                [message['From'][0][1]] + \
                [msg[1] for msg in message['To'] if
                    msg[1] != setup['address']]
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'reply_all'})

        def forward():
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'forward'})

        handlers.connect_button(script, "button_reply", reply)
        handlers.connect_button(script, "button_reply_all", reply_all)
        handlers.connect_button(script, "button_forward", forward)

        def change_msg(direction):
            ids_list = data['msg_ids_list']
            new_msg_id = ids_list[(ids_list.index(data['message_uid']) +
                                  direction) % len(ids_list)]
            data.update({'message_uid': new_msg_id})
            window.load_view('email/single_message', data)

        handlers.connect_button(script, "button_next_mail",
                                change_msg, 1)
        handlers.connect_button(script, "button_previous_mail",
                                change_msg, -1)

email_app = {
    "app": "email",
    "type": "clutter",
    "elements": ELEMENTS,
    "views": [
        ("main", prepare_main_view),
        ("drafts", prepare_drafts_view),
        ("inbox", prepare_inbox_view),
        ("sent", prepare_sent_view),
        ("single_message", prepare_single_message_view),
        ("address_book", prepare_address_book_view),
        ("contact", prepare_contact_view),
        ("speller_message_body", prepare_speller_message_body_view),
        ("speller_message_to", prepare_speller_message_to_view),
        ("speller_message_subject", prepare_speller_message_subject_view),
        ("speller_contact_name", prepare_speller_contact_name_view),
        ("speller_contact_address", prepare_speller_contact_address_view),
        ("viewer_contact_library", prepare_viewer_contact_library_view),
        ("viewer_contact_album", prepare_viewer_contact_album_view)
    ]
}
