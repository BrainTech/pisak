#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name = 'PISAK',
    version = '1.0',
    description = 'Polish Integrational System for Alternative Communication',
    long_description = ''
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
