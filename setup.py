#!/usr/bin/env python3

from distutils.core import setup

setup(name='PISAK',
      version='1.0',
      description='Polish Integrational System for Alternative Communication',
      long_description=''
      author='doc.pisak.org/authors.html',
      author_email='contact@pisak.org',
      url='http://pisak.org/',
      packages=['pisak', 'pisak.libs', 'pisak.libs.audio',
                'pisak.libs.blog', 'pisak.libs.email', 'pisak.libs.movie',
                'pisak.libs.paint', 'pisak.libs.speller',
                'pisak.libs.symboler', 'pisak.libs.viewer'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Communications',
          ],
)
