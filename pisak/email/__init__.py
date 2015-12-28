def test(config):
    """
    Test provided email settings or server connection.
    """
    import socket

    from pisak import exceptions
    from pisak.loc import EMAIL_MESSAGES as MESSAGES
    from pisak.email.test_connection import test_smtp_connection
    from pisak.email.imap_client import IMAPClient, InvalidCredentialsError

    socket.setdefaulttimeout(5)

    try:
        dummy_client = IMAPClient(config)
        dummy_client.login()
        dummy_client.logout()

        test_smtp_connection(config)
    except (socket.timeout, exceptions.NoInternetError):
        ret = False, MESSAGES['no_internet']
    except InvalidCredentialsError:
        ret = False, MESSAGES['invalid_credentials']
    except IMAPClientError:
        ret = False, MESSAGES['IMAP_failed']
    except EmailSendingError:
        ret = False, MESSAGES['SMTP_failed']
    except Exception:
        ret = False, MESSAGES['unknown']
    else:
        ret = True, MESSAGES['success']

    socket.setdefaulttimeout(None)

    return ret