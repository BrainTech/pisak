"""
Module providing access to the email account through the imap client.
"""
import socket
import imaplib
import email
import time
import functools

from pisak import logger, exceptions
from pisak.email import config, parsers


# monkeypatch because of too low limit set by default in the std module,
# that has not been accommodated to the modern world standards yet.
imaplib._MAXLINE = 1000000


_LOG = logger.get_logger(__name__)


class IMAPClientError(exceptions.PisakException):
    ...


class MailboxNotFoundError(IMAPClientError):
    ...


class InvalidCredentialsError(IMAPClientError):
    ...


def _imap_errors_handler(custom_error):
        """
        Decorator. Handles errors related to IMAP server connection.

        :param custom_error: error type that should be thrown
        when any IMAP related error is ecountered.
        """
        def wrapper(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except socket.error as exc:
                    raise exceptions.NoInternetError(exc) from exc
                except imaplib.IMAP4.error as exc:
                    raise custom_error(exc) from exc
            return handler
        return wrapper


MAILBOX_HEADERS = {
    "inbox": ["Subject", "From", "Date"],
    "sent_box":  ["Subject", "To", "Date"]
}


class IMAPClient(object):
    """
    Class representing an email account connection.
    Used access protocol - IMAP.
    """
    def __init__(self, custom_config=None):
        self._conn = None
        self._positive_response_code = "OK"
        self._setup = custom_config or config.Config().get_account_setup()
        self._sent_box_name = self._setup["sent_folder"]

    @_imap_errors_handler(IMAPClientError)
    def login(self):
        server_in = self._setup["IMAP_server"]
        port_in = self._setup["IMAP_port"]
        if port_in == "993":
            self._conn = imaplib.IMAP4_SSL(
                server_in, port=port_in,
                keyfile=self._setup.get("keyfile"),
                certfile=self._setup.get("certfile")
            )
        else:
            if port_in != "143":
                msg = "Port {} is not valid for IMAP protocol. " \
                      "Trying through 143."
                _LOG.warning(msg.format(port_in))
                port_in = "143"
            self._conn = imaplib.IMAP4(server_in, port=port_in)
        self._do_login()

    @_imap_errors_handler(InvalidCredentialsError)
    def _do_login(self):
        self._conn.login(self._setup["address"],
                         self._setup["password"])

    @_imap_errors_handler(IMAPClientError)
    def logout(self):
        """
        Logout from the account.
        """
        if self._conn is not None:
            self._conn.close()
            self._conn.logout()
        else:
            _LOG.warning("There is no connection to the email account."
                         "Nowhere to logout from.")

    def get_inbox_status(self):
        """
        Get number of all messages in the inbox and
        number of the unseen messages.

        :returns: tuple with two integers: number of all messages
        and number of unseen messages; or False on query failure.
        """
        return self._get_mailbox_status("INBOX")

    def get_sent_box_count(self):
        """
        Get number of all messages in the sent box.

        :returns: integers with number of all messages;
        or False on query failure.
        """
        return self._get_mailbox_count(self._sent_box_name)

    def get_message_from_inbox(self, id):
        """
        Get message with the given id from the inbox.

        :param id: id of the message.

        :return: dictionary with the message; or False on query failure.
        """
        return self._get_message("INBOX", id)

    def get_message_from_sent_box(self, id):
        """
        Get message with the given id from the box of sent messages.

        :param id: id of the message.

        :return: dictionary with the message; or False on query failure.
        """
        return self._get_message(self._sent_box_name, id)

    def get_many_messages_from_inbox(self, ids):
        """
        Get many messages with the given ids from the inbox.

        :param ids: list of ids of the messages.

        :return: list of dictionaries with the messages; or False on query failure.
        """
        return self._get_many_messages("INBOX", ids)

    def get_many_messages_from_sent_box(self, ids):
        """
        Get messages with the given ids from the box of sent messages.

        :param ids: list of ids of the messages.

        :return: list of dictionaries with the messages; or False on query failure.
        """
        return self._get_many_messages(self._sent_box_name, ids)

    def get_many_previews_from_inbox(self, ids):
        """
        Get many previews with the given ids from the inbox.

        :param ids: list of ids of the messages.

        :return: list of dictionaries with the previews; or False on query failure.
        """
        return self._get_many_previews("INBOX", ids,
                                       MAILBOX_HEADERS["inbox"])

    def get_many_previews_from_sent_box(self, ids):
        """
        Get previews with the given ids from the box of sent messages.

        :param ids: list of ids of the previewss.

        :return: list of dictionaries with the previews; or False on query failure.
        """
        return self._get_many_previews(self._sent_box_name, ids,
                                       MAILBOX_HEADERS["sent_box"])

    def get_inbox_list(self):
        """
        Get list containing previews of all the messages.

        :returns: list of dictionary with message previews, each containing:
        subject, sender and date; or False on query failure.
        """
        return self._get_mailbox_list("INBOX", MAILBOX_HEADERS["inbox"])

    def get_sent_box_list(self):
        """
        Get list containing previews of all the sent messages.

        :returns: list of dictionary with message previews, each containing:
        subject, sender and date; or False on query failure.
        """
        return self._get_mailbox_list(self._sent_box_name,
                                      MAILBOX_HEADERS["sent_box"])

    def delete_message_from_inbox(self, id):
        """
        Permanently delete the given message from the inbox.

        :param id: unique id of the message.
        """
        self._delete_message("INBOX", id)

    def delete_message_from_sent_box(self, id):
        """
        Permanently delete the given message from the sent box.

        :param id: unique id of the message.
        """
        self._delete_message(self._sent_box_name, id)

    def get_inbox_ids(self):
        """
        Get a list of ids of all the messages in the inbox.

        :return: list of ids; or False on query failure.
        """
        return self._get_ids("INBOX")

    def get_sent_box_ids(self):
        """
        Get a list of ids of all the messages in the sent box.

        :return: list of ids; or False on query failure.
        """
        return self._get_ids(self._sent_box_name)

    @_imap_errors_handler(IMAPClientError)
    def _get_ids(self, mailbox):
        self._conn.select(mailbox)
        res, ids_data = self._conn.search(None, "ALL")
        if res != self._positive_response_code:
            ret = False
        else:
             ret = ids_data[0].decode(
                     parsers.DEFAULT_CHARSET, "replace").split()
        return list(reversed(ret))

    @_imap_errors_handler(IMAPClientError)
    def _delete_message(self, mailbox, id):
        self._conn.select(mailbox)
        self._conn.store(id, "+FLAGS", "\\Deleted")
        self._conn.expunge()

    @_imap_errors_handler(IMAPClientError)
    def _get_mailbox_list(self, mailbox, headers):
        self._conn.select(mailbox)
        res, ids_data = self._conn.search(None, "ALL")
        if res != self._positive_response_code:
            ret = False
        else:
            ids = ids_data[0].decode(parsers.DEFAULT_CHARSET, "replace").split()
            res, msg_data = self._conn.fetch(
                ",".join(ids),
                "(BODY.PEEK[HEADER.FIELDS ({})])".format(" ".join(headers).upper()))
            if res != self._positive_response_code:
                ret = False
            else:
                ret = parsers.parse_mailbox_list(ids, msg_data, headers)
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _get_many_previews(self, mailbox, ids, headers):
        self._conn.select(mailbox)
        res, previews_data = self._conn.fetch(
                ",".join(ids),
                "(BODY.PEEK[HEADER.FIELDS ({})])".format(
                        " ".join(headers).upper()))
        if res != self._positive_response_code:
            ret = False
        else:
            ret = parsers.parse_mailbox_list(ids, previews_data, headers)
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _find_mailboxes(self):
        """
        It is strongly advised not to use this method right now.
        """
        res, mailboxes_data = self._conn.list()
        if res != self._positive_response_code:
            return False
        else:
            for mailbox in mailboxes_data:
                mailbox = mailbox.decode(parsers.DEFAULT_CHARSET, "replace")
                if "sent" in mailbox.lower():
                    self._sent_box_name = mailbox.split()[-1].split('"')[1]

    @_imap_errors_handler(IMAPClientError)
    def _get_message(self, mailbox, id):
        self._conn.select(mailbox)
        res, msg_data = self._conn.fetch(id, '(RFC822)')
        if res != self._positive_response_code:
            ret = False
        else:
            ret =  parsers.parse_message(
                msg_data[0][1].decode(parsers.DEFAULT_CHARSET, "replace"))
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _get_many_messages(self, mailbox, ids):
        ids = ' ,'.join(ids)
        self._conn.select(mailbox)
        res, msgs_data = self._conn.fetch(ids, '(RFC822)')
        if res != self._positive_response_code:
            ret = False
        else:
            ret = []
            for msg in msgs_data[0][1]:
                ret.append(parsers.parse_message(
                    msg.decode(parsers.DEFAULT_CHARSET, "replace")))
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _get_mailbox_count(self, mailbox):
        self._conn.select(mailbox)
        res, ids_data = self._conn.search(None, "ALL")
        if res != self._positive_response_code:
            ret = False
        else:
            ret = len(ids_data[0].decode(
                parsers.DEFAULT_CHARSET, "replace").split())
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _get_mailbox_status(self, mailbox):
        res, status_data = self._conn.status(mailbox, "(MESSAGES UNSEEN)")
        if res != self._positive_response_code:
            ret = False
        else:
            status = status_data[0].decode(parsers.DEFAULT_CHARSET, "replace")
            ret =  int(status[status.find("MESSAGES") : ].split()[1]), \
               int(status[status.find("UNSEEN") : ].split()[1].rstrip(")"))
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _append_to_mailbox(self, mailbox, message):
        res, _query_ret  = self._conn.append(
                 mailbox, "", imaplib.Time2Internaldate(time.time()),
                message.as_string())
        return res == self._positive_response_code

    @_imap_errors_handler(IMAPClientError)
    def _create_mailbox(self, mailbox):
        res, _query_ret  = self._conn.create(mailbox)
        return res == self._positive_response_code
