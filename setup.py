#!/usr/bin/env python3

from setuptools import setup, find_packages

VERSION = '1.0'

setup(
    name = 'pisak',
    version = VERSION,
    description = 'Polish Integrational System for Alternative Communication',
    long_description = '''PISAK is a programme for people with severe 
    problems of muscle control. It lets them operate various applications
    (speller, email, blog, audio, video, etc.- see the site for the full list)
    using only one signal which might be send through a switch, puff, EMG. 
    PISAK is also a library which helps to write applications that work 
    according to above description.
    Applications in PISAK can be also operated using an eyetracker or a
    conventional mouse.''',
    author = 'Aleksander Kijek',
    author_email = 'sasza@braintech.pl',
    keywords = 'aac disability communication assistive control computer',
    url = 'http://pisak.org/',
    packages = find_packages(),
    license = 'GPLv3',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
    ],
    scripts = ['bin/pisak', 'bin/pisak-audio', 'bin/pisak-blog',
               'bin/pisak-email', 'bin/pisak-movie', 'bin/pisak-paint',
               'bin/pisak-speller', 'bin/pisak-symboler', 'bin/pisak-viewer'],
    zip_safe = False,
    include_package_data = True,
    install_requires = ['pressagio', 'pydenticon', 'ezodf',
                        'python-wordpress-xmlrpc']
)
