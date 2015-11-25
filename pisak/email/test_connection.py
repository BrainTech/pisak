import socket
import smtplib
from ssl import SSLError

from pisak import exceptions
from pisak.email import config
from pisak.email.message import EmailSendingError


def test_smtp_connection(custom_config=None):
    """
    Test SMTP connection.
    """
    setup = custom_config or config.Config().get_account_setup()
    server_out = "{}:{}".format(
            setup["SMTP_server"], setup["SMTP_port"])
    try:
        server = smtplib.SMTP(server_out)
        server.ehlo_or_helo_if_needed()
        if server.has_extn("STARTTLS"):
            server.starttls(
                keyfile=setup.get("keyfile"), certfile=setup.get("certfile"))
        server.ehlo_or_helo_if_needed()
        server.login(setup["address"], setup["password"])
        server.quit()
    except socket.error as exc:
        raise exceptions.NoInternetError(exc) from exc
    except (smtplib.SMTPException, SSLError) as exc:
        raise EmailSendingError(exc) from exc