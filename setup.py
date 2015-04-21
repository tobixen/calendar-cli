#!/usr/bin/env python

import sys
import os

from setuptools import setup, find_packages

## TODO: "import imp" will not work from python 3.3, ref
## http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path.
## Since we depend on caldav which depends on vobject which currently
## doesn't support python3, it's not an issue right now.
import imp
my_script = imp.load_source('my_script', './calendar-cli.py')
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
        #"License :: OSI Approved :: ...",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
    ],
    scripts=['calendar-cli.py'],
    install_requires=[
        'icalendar',
        'caldav>=0.4.0.dev',
        'pytz',
        'tzlocal'
    ],
   **metadata
)
