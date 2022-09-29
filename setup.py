#!/usr/bin/env python

import sys
import os

from setuptools import setup, find_packages

import calendar_cli as my_script

metadata = {}
for attribute in ('version', 'author', 'author_email', 'license'):
    if hasattr(my_script, '__%s__' % attribute):
        metadata[attribute] = getattr(my_script, '__%s__' % attribute)

setup(
    name='calendar-cli',
    description='Simple command-line CalDav client, for adding and browsing calendar items, todo list items, etc.',
    url='https://github.com/tobixen/calendar-cli',
    #packages=['',
    #          ],
    classifiers=[
        #"Development Status :: ..."
        "Environment :: Web Environment",
        #"Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
    ],
    scripts=['calendar-cli.py', 'calendar-cli'],
    py_modules=['cal'],
    install_requires=[
        'icalendar',
        'caldav>=0.10.0dev',
#        'isodate',
        'pytz', ## pytz is supposed to be obsoleted, but see https://github.com/collective/icalendar/issues/333 
        'tzlocal',
        'Click',
        'six'
    ],
    entry_points={
        'console_scripts': [
            'kal = cal:cli',
        ],
    },
   **metadata
)
