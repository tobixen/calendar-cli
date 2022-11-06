#!/usr/bin/env python

import sys
import os

from setuptools import setup, find_packages

from calendar_cli.metadata import metadata
metadata_ = metadata.copy()

for x in metadata:
    if not x in ('author', 'version', 'license', 'maintainer', 'author_email',
                 'status', 'name', 'description', 'url', 'description'):
        metadata_.pop(x)

setup(
    packages=['calendar_cli',
              ],
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
    scripts=['bin/calendar-cli.py', 'bin/calendar-cli'],
    py_modules=['cal'],
    install_requires=[
        'icalendar',
        'caldav>=0.10',
#        'isodate',
        'pytz', ## pytz is supposed to be obsoleted, but see https://github.com/collective/icalendar/issues/333 
        'tzlocal',
        'Click',
        'six'
    ],
    entry_points={
        'console_scripts': [
            'kal = calendar_cli.cal:cli',
        ],
    },
   **metadata_
)
