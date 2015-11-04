"""
i18n tools.
"""


# all the mappings will be bidirectional, check below
CONFIG_MAPS = {
    'SKIN': {
        'default': 'domyślna',
        'turquoise': 'turkusowa'},
    'INPUT': {
        'mouse-switch': 'przycisk',
        'pisak-switch': 'przycisk PISAK',
        'mouse': 'myszka',
        'keyboard': 'klawiatura (spacja)',
        'eyetracker': 'okulograf',
        'tobii': 'tobii',
        'eviacam': 'eviacam',
        'eyetracker-no-correction': 'okulograf bez korekcji',
        'eyetracker-mockup': 'okulograf testowy'},
    'REACT_ON': {
        'press': 'wciśnięcie',
        'release': 'odpuszczenie'},
    'SPELLER_LAYOUT': {
        'default': 'domyślny',
        'alphabetical': 'alfabetyczny',
        'frequency': 'częstotliwościowy'}
}

# make the mappings bidirectional
for dic in CONFIG_MAPS.values():
    for key, value in list(dic.items()):
        dic[value] = key


EMAIL_MESSAGES = {
    'no_internet': 'Brak połączenia z internetem.\nSprawdź swoje łącze i spróbuj ponownie.',
    'invalid_credentials': 'Nieprawidłowy adres e-mail lub hasło.\n'
                           'Sprawdź wprowadzone dane i spróbuj ponownie.',
    'SMTP_failed': 'Błąd połączenia z serwerem SMTP.\nSprawdź wprowadzone dane,\n'
                   ' zwłaszcza port i nazwę serwera SMTP i spróbuj ponownie.',
    'IMAP_failed': 'Błąd połączenia z serwerem IMAP.\nSprawdź wprowadzone dane,\n'
                   ' zwłaszcza port i nazwę serwera IMAP i spróbuj ponownie.',
    'unknown': 'Błąd weryfikacji.\nSprawdź wszystkie wprowadzone dane '
               'i spróbuj ponownie.',
    'success': 'Wszystko OK.\nWprowadzone dane są prawidłowe.'
}


BLOG_MESSAGES = {
    'no_internet': 'Brak połączenia z internetem.\nSprawdź swoje łącze i spróbuj ponownie.',
    'invalid_credentials': 'Nieprawidłowa nazwa użytkownika lub hasło.\n'
                           'Sprawdź wprowadzone dane i spróbuj ponownie.',
    'unknown': 'Błąd weryfikacji.\nSprawdź wszystkie wprowadzone dane '
               'i spróbuj ponownie.',
    'no_such_blog': 'Blog nie istnieje. Jeśli chcesz założyć swojego bloga '
                    'skontaktuj się z obsługą techniczną.',
    'success': 'Wszystko OK.\nWprowadzone dane są prawidłowe.'
}