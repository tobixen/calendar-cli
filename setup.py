#!/usr/bin/env python

import sys
import os

from setuptools import setup, find_packages

## TODO: "import imp" will not work from python 3.3, ref
## http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path.
## Since we depend on caldav which depends on vobject which currently
## doesn't support python3, it's not an issue right now.
## but it is an issue that the purpose of this script is to enable installation of dependencies,
## and if the dependencies doesn't exist, this import breaks!  TODO ...
metadata = {}
import imp
try:
    my_script = imp.load_source('my_script', './calendar-cli.py')
    for attribute in ('version', 'author', 'author_email', 'license'):
        if hasattr(my_script, '__%s__' % attribute):
            metadata[attribute] = getattr(my_script, '__%s__' % attribute)
except:
    pass

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
    install_requires=[
        'icalendar',
        'caldav>=0.5.0',
        'pytz',
        'tzlocal'
    ],
   **metadata
)
