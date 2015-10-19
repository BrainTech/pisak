def test():
    """
    Test provided email settings or server connection.
    """
    from pisak.email.message import SimpleMessage
    from pisak.email.imap_client import IMAPClient

    ERRORS = {
        0: 'Brak połączenia z internetem. Sprawdź swoje łącze internetowe i spróbuj jeszcze raz.',
        1: 'Nieprawidłowe hasło.',
        2: 'Nieprawidłowy adres email.'
    }

    dummy_msg = SimpleMessage()
    dummy_client = IMAPClient()