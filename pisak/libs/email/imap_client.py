"""
Module providing access to the email account through the imap client.
"""
import socket
import imaplib
import email
import time

from pisak import logger, exceptions
from pisak.libs.email import config, parsers


# monkeypatch because of too low limit set by default in the std module,
# that has not been accommodated to the modern world standards yet.
imaplib._MAXLINE = 1000000


_LOG = logger.get_logger(__name__)


class IMAPClientError(exceptions.PisakException):
    ...


class MailboxNotFoundError(IMAPClientError):
    ...


class InvalidCredentials(IMAPClientError):
    ...


def _imap_errors_handler(custom_error):
        """
        Decorator. Handles errors related to IMAP server connection.

        :param custom_error: error type that should be thrown
        when any IMAP related error is ecountered.
        """
        def wrapper(func):
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
    def __init__(self):
        self._conn = None
        self._positive_response_code = "OK"
        self._config_obj = config.Config()
        self._setup = self._config_obj.get_account_setup()
        self._sent_box_name = self._setup["sent_box_name"]

    @_imap_errors_handler(IMAPClientError)
    def login(self):
        server_in = "imap.{}".format(self._setup["server_address"])
        port_in = self._setup["port_in"]
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

    @_imap_errors_handler(InvalidCredentials)
    def _do_login(self):
        self._conn.login(self._setup["user_address"],
                         self._config_obj.decrypt_password(self._setup["password"]))

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

    def get_message_from_inbox(self, uid):
        """
        Get message with the given uid from the inbox.

        :param uid: uid of the message.

        :return: dictionary with the message; or False on query failure.
        """
        return self._get_message("INBOX", uid)

    def get_message_from_sent_box(self, uid):
        """
        Get message with the given uid from the box of sent messages.

        :param uid: uid of the message.

        :return: dictionary with the message; or False on query failure.
        """
        return self._get_message(self._sent_box_name, uid)

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

    def delete_message_from_inbox(self, uid):
        """
        Permanently delete the given message from the inbox.

        :param uid: unique id of the message.
        """
        self._delete_message("INBOX", uid)

    def delete_message_from_sent_box(self, uid):
        """
        Permanently delete the given message from the sent box.

        :param uid: unique id of the message.
        """
        self._delete_message(self._sent_box_name, uid)

    @_imap_errors_handler(IMAPClientError)
    def _delete_message(self, mailbox, uid):
        self._conn.select(mailbox)
        self._conn.store(uid, "+FLAGS", "\\Deleted")
        self._conn.expunge()

    @_imap_errors_handler(IMAPClientError)
    def _get_mailbox_list(self, mailbox, headers):
        self._conn.select(mailbox)
        res, uids_data = self._conn.search(None, "ALL")
        if res != self._positive_response_code:
            ret = False
        else:
            uids = uids_data[0].decode(
                parsers.DEFAULT_CHARSET, "replace").split()
            res, msg_data = self._conn.fetch(
                ",".join(uids),
                "(BODY.PEEK[HEADER.FIELDS ({})])".format(
                    " ".join(headers).upper())
            )
            if res != self._positive_response_code:
                ret = False
            else:
                ret = parsers.parse_mailbox_list(uids, msg_data, headers)
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
    def _get_message(self, mailbox, uid):
        self._conn.select(mailbox)
        res, msg_data = self._conn.fetch(uid, '(RFC822)')
        if res != self._positive_response_code:
            ret = False
        else:
            ret =  parsers.parse_message(
                msg_data[0][1].decode(parsers.DEFAULT_CHARSET, "replace"))
        return ret

    @_imap_errors_handler(IMAPClientError)
    def _get_mailbox_count(self, mailbox):
        self._conn.select(mailbox)
        res, uids_data = self._conn.search(None, "ALL")
        if res != self._positive_response_code:
            ret = False
        else:
            ret = len(uids_data[0].decode(
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
                 mailbox, "", imaplib.Time2Internaldate(time()),
                message.as_string())
        return res == self._positive_response_code

    @_imap_errors_handler(IMAPClientError)
    def _create_mailbox(self, mailbox):
        res, _query_ret  = self._conn.create(mailbox)
        return res == self._positive_response_code
