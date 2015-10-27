"""
i18n tools.
"""


# all the mappings will be bidirectional, check below
MAPS = {
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
for dic in MAPS.values():
    for key, value in list(dic.items()):
        dic[value] = key