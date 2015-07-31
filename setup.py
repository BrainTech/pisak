#!/usr/bin/env python3

from distutils.core import setup

setup(name='PISAK',
      version='1.0',
      description='Polish Integrational System for Alternative Communication',
      author='doc.pisak.org/authots.html',
      url='http://pisak.org/',
      packages=['pisak', 'pisak.libs'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Topic :: Documentation :: Sphinx',
          ],
)
