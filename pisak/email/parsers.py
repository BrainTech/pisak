"""
Email parsers.
"""
import email
import time
from datetime import datetime

from pisak import logger


_LOG = logger.get_logger(__name__)


DEFAULT_CHARSET = "utf-8"


def _decode_message(message):
    """
    Decode content of the message.

    :param message: non-multipart message object.

    :return: decoded content of the message
    """
    content = message.get_payload(decode=True)
    charset = message.get_content_charset(DEFAULT_CHARSET)
    return content.decode(charset, "replace")


def _get_addresses(value, header=None):
    """
    Extract all addresses from a header with the given name.

    :params value: single string with raw header value or
    `email.message.Message` instance.
    :param header: header name, obligatory when 'value' is an
    `email.message.Message` instance.

    :returns: in case when 'value' param is an `email.message.Message`instance
    then returns list of tuples containing name and address for each record,
    if 'value' is a string then returns a single tuple of this kind.
    """
    if isinstance(value, str):
        return email.utils.parseaddr(value)
    elif isinstance(value, email.message.Message):
        return email.utils.getaddresses(value.get_all(header, []))
    else:
        _LOG.error("Invalid argument 'value'. Only string or "
                   "'email.message.Message' instance are accepted.")


def _parse_date(raw_date):
    """
    Parse date of the message.

    :param raw_date: raw date string.

    :returns: datetime object or None in case of parsing failure
    """
    date_tuple = email.utils.parsedate(raw_date)
    return datetime.fromtimestamp(time.mktime(date_tuple)) \
            if date_tuple else None


def _decode_header(header):
    """
    Decode the given header with charsets supplied within or
    with the default charset.

    :param header: raw header.

    :returns: single string with a decoded header.
    """
    try:
        headers = email.header.decode_header(header)
    except email.errors.HeaderParseError:
        return header.encode(DEFAULT_CHARSET, "replace").decode(
            DEFAULT_CHARSET, "replace")
    else:
        for idx, (value, charset) in enumerate(headers):
            if isinstance(value, bytes):
                headers[idx] = value.decode(
                    charset or DEFAULT_CHARSET, "replace")
            elif isinstance(value, str):
                headers[idx] = value.encode(
                    charset or DEFAULT_CHARSET, "replace").decode(
                    charset or DEFAULT_CHARSET, "replace")
        return "".join(headers)


def parse_message(raw_message):
    """
    Parse the given raw message.

    :param raw_message: single string with the whole  raw message.

    :returns: dictionary containing all fields of parsed message.
    """
    parsed_msg = {}
    msg = email.message_from_string(raw_message)

    content_type = msg.get_content_maintype()
    body = []
    # look for plain text message body
    if content_type == "multipart":
        for part in msg.walk():
            is_inline = part.get("Content-Disposition") in (None, "inline")
            if part.get_content_type() == "text/plain" and is_inline:
                body.append(_decode_message(part))
    elif content_type in ("text/plain", "text"):
        body.append(_decode_message(msg))
    parsed_msg["Body"] = "\n".join(body)

    # put all the message fields into a dictionary
    parsed_msg.update(msg.items())

    # look for all the addresses
    parsed_msg["To"] = _get_addresses(msg, "To")
    parsed_msg["From"] = _get_addresses(msg, "From")

    # decode some headers that may need that
    for header in ["Subject", "Date", "Message-ID"]:
        if header in parsed_msg:
            parsed_msg[header] = _decode_header(parsed_msg.get(header))

    # convert date into datetime object if possible
    date = _parse_date(parsed_msg.get("Date"))
    if date:
        parsed_msg["Date"] = date

    return parsed_msg


def parse_mailbox_list(ids, msg_data, headers):
    """
    Parse list of message previews.

    :param ids: list of the given messages ids.
    :param msg_data: raw messages data.
    :param headers: list of headers to be parsed.

    :returns: list of dictionaries containing parsed message previews.
    """
    mailbox_list = []
    for idx, (_spec, msg) in enumerate(reversed(msg_data[::2])):
        parsed_msg = {"UID": ids[idx]}
        str_msg = msg.decode(DEFAULT_CHARSET, "replace")
        for header_name in headers:
            parsed_header = _decode_header(str_msg[
                str_msg.find(header_name) + len(header_name)+1: ].split("\r\n")[0])
            if header_name == "Date":
                parsed_msg[header_name] = _parse_date(parsed_header) or \
                                          parsed_header
            elif header_name in ("From", "To"):
                parsed_msg[header_name] = _get_addresses(parsed_header, header_name)
            else:
                parsed_msg[header_name] = parsed_header
        mailbox_list.append(parsed_msg)
    return mailbox_list
