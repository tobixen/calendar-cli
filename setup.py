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
    dependency_links = [
        # The package doesn't seem to be on pypi.
        # We assume a low version number in case it gets uploaded
        # so that the higher version is chosen over the git version
        #
        # There is a mirror here:
        'https://github.com/skarra/CalDAVClientLibrary/tarball/master#egg=caldavclientlibrary-0.0.1',
        'git+https://github.com/skarra/CalDAVClientLibrary.git#egg=caldavclientlibrary-0.0.1',
        # We should prefer the official SVN
        'svn+http://svn.calendarserver.org/repository/calendarserver/CalDAVClientLibrary/trunk#egg=caldavclientlibrary-0.0.2',
        # But there is an issue with the upstream setup.py, it does not have a name=''
        # So we load the patched version
        'git+https://github.com/muelli/CalDAVClientLibrary.git#egg=caldavclientlibrary-0.0.3',
    ],
    install_requires=[
        'icalendar',
        'caldavclientlibrary',
    ],
)
