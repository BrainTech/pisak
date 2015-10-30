def test(config):
    """
    Test provided blog settings or server connection.
    """
    from pisak.blog.wordpress import _OwnBlog
    from pisak.blog import exceptions

    MESSAGES = {
        'no_internet': 'Brak połączenia z internetem.\nSprawdź swoje łącze i spróbuj ponownie.',
        'invalid_credentials': 'Nieprawidłowa nazwa użytkownika lub hasło.\n'
                               'Sprawdź wprowadzone dane i spróbuj ponownie.',
        'unknown': 'Błąd weryfikacji.\nSprawdź wszystkie wprowadzone dane '
                   'i spróbuj ponownie.',
        'no_such_blog': 'Blog nie istnieje. Jeśli chcesz założyć swojego bloga '
                        'skontaktuj się z obsługą techniczną.',
        'success': 'Wszystko OK.\nWprowadzone dane są prawidłowe.'
    }

    try:
        dummy_blog = _OwnBlog(config)
    except exceptions.BlogInternetError:
        ret = False, MESSAGES['no_internet']
    except exceptions.BlogAuthenticationError:
        ret = False, MESSAGES['invalid_credentials']
    except Exception:
        ret = False, MESSAGES['unknown']
    else:
        ret = True, MESSAGES['success']
    return ret