#!/usr/bin/env python

import sys
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='calendar-cli',
    version='0.1',
    description='Simple command-line CalDav client, for adding and browsing calendar items, todo list items, etc.',
    url='https://github.com/tobixen/calendar-cli',
    #packages=['',
    #          ],
    license='GPLv3+',
    author='Tobias Brox',
    author_email='t-calendar-cli@tobixen.no',
    classifiers=[
        #"Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        #"License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    scripts=['calendar-cli.py'],
    install_requires=[
        'icalendar',
        'caldav>=0.2',
        'pytz',
        'tzlocal'
    ],
)
