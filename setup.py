#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name = 'PISAK',
    version = '1.0',
    description = 'Polish Integrational System for Alternative Communication',
    long_description = '''PISAK is a programme for people with severe 
    problems of muscle control. It lets them operate various applications
    (speller, email, blog, audio, video, etc.- see the site for the full list)
    using only one signal which might be send through a switch, puff, EMG. 
    PISAK is also a library which helps to write applications that work 
    according to above description.
    Applications in PISAK can be also operated using an eyetracker or a
    conventional mouse.''',
    author = 'doc.pisak.org/authors.html',
    author_email = 'contact@pisak.org',
    url = 'http://pisak.org/',
    packages = find_packages() 
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Communications',
    ],
    scripts = ['bin/pisak', 'bin/pisak-audio', 'bin/pisak-blog',
               'bin/pisak-email', 'bin/pisak-movie', 'bin/pisak-paint',
               'bin/pisak-speller', 'bin/pisak-symboler', 'bin/pisak-viewer']
)
