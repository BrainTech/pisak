def test(config):
    """
    Test provided email settings or server connection.
    """
    from pisak import exceptions
    from pisak.email.message import SimpleMessage
    from pisak.email.imap_client import IMAPClient, InvalidCredentialsError

    MESSAGES = {
        'no_internet': 'Brak połączenia z internetem.\nSprawdź swoje łącze i spróbuj ponownie.',
        'invalid_credentials': 'Nieprawidłowy adres e-mail lub hasło.\n'
                               'Sprawdź wprowadzone dane i spróbuj ponownie.',
        'unknown': 'Błąd weryfikacji.\nSprawdź wszystkie wprowadzone dane '
                   'i spróbuj ponownie.',
        'success': 'Wszystko OK.\nWprowadzone dane są prawidłowe.'
    }

    try:
        dummy_client = IMAPClient(config)
        dummy_client.login()
        dummy_client.logout()

        dummy_msg = SimpleMessage()
        dummy_msg.test(config)
    except exceptions.NoInternetError:
        ret = False, MESSAGES['no_internet']
    except InvalidCredentialsError:
        ret = False, MESSAGES['invalid_credentials']
    except Exception:
        ret = False, MESSAGES['unknown']
    else:
        ret = True, MESSAGES['success']
    return ret