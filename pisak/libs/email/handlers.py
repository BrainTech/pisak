"""
Email application specific signal handlers.
"""
from pisak import exceptions
from pisak.apps.email.app import MESSAGES
from pisak.libs import signals
from pisak.libs.email import message


@signals.registered_handler("email/new_message_add_subject")
def add_subject(text_box, app):
    """
    Add subject to the new message.

    :param text_box: text box with a message subject.
    :param app: application instance that stores the message that is being
    created.
    """
    app.box["new_message"].subject = text_box.get_text()


@signals.registered_handler("email/new_message_add_body")
def add_body(text_box, app):
    """
    Add body to the new message.

    :param text_box: text box with a message body.
    :param app: application instance that stores the message that is being
    created.
    """
    app.box["new_message"].body = text_box.get_text()


@signals.registered_handler("email/new_message_send")
def send(source, app):
    """
    Send the new message.

    :param source: source of a signal that triggered this function.
    :param app: application instance that stores the message
    that should be send.
    """
    try:
        app.box["new_message"].send()
    except message.EmailSendingError as e:
        app.window.load_popup(MESSAGES["message_send_fail"], "email/main")
    except exceptions.NoInternetError as e:
        app.window.load_popup(MESSAGES["no_internet"], "email/main")

    app.box["new_message"].clear()
