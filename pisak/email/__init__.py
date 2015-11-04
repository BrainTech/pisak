def test(config):
    """
    Test provided email settings or server connection.
    """
    from pisak import exceptions
    from pisak.loc import EMAIL_MESSAGES as MESSAGES
    from pisak.email.message import test_smtp_connection
    from pisak.email.imap_client import IMAPClient, InvalidCredentialsError

    try:
        dummy_client = IMAPClient(config)
        dummy_client.login()
        dummy_client.logout()

        test_smtp_connection(config)
    except exceptions.NoInternetError:
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
    return ret