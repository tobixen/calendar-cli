calendar-cli
============

Simple command-line CalDav client, for adding and browsing calendar items, todo list items, etc

Rationale
---------

GUIs and Web-UIs are nice for some purposes, but I really find the command line unbeatable when it comes to:

* Minor stuff that are repeated often.  Writing something like "todo add make a calendar-cli system" or "cal add 'tomorrow 15:40+2h' doctor appointment" is just very much faster than navigating into some web calendar interface and add an item there.
* Things that are outside the scope of the UI.  Here is one of many tasks I'd like to do: "go through the work calendar, find all new calendar events that are outside office hours, check up with the personal calendar if there are potential conflicts, add some information at the personal calendar if appropriate", and vice versa - it has to be handled very manually if doing it through any normal calendar application as far as I know, but if having some simple CLI or python library I could easily make some interactive script that would help me doing the operation above.

I've been looking a bit around, all I could find was cadaver and CalDAVClientLibrary.  Both of those seems to be a bit shortcoming; they seem to miss the iCalendar parsing/generation.  CalDAVClientLibrary is already a python library, and there also exist python libraries for iCalendar parsing/generation, so all that seems to be missing is the "glue" between those libraries.

Synopsis
--------

    calendar-cli.py [global options] [command] [command options] [subcommand] [subcommand options] [subcommand arguments] ...

cli.py should be symlinked to the various commands.

A configuration file (ini-format?) can contain defaults for all the global options.

The config file may have a section for each CalDAV server ... (todo, think more about this)

### Global options

(only long options will be available in version 0.1; don't want to pollute the short option space yet)

* --interactive, -i: stop and query the user rather often
* --caldav-host, --caldav-user, --caldav-pass: how to connect to the CalDAV server
* --caldav-calendar: which calendar to access
* --config: use a specific configuration file (default: $HOME/.calendar-cli.conf)
* --config-section: use a specific section from the config file (i.e. to select a different 
* --icalendar: instead of connecting to a CalDAV server, write an icalendar file to stdout

### Commands

* cal - access/modify a calendar
    * subcommands: add, agenda
* todo - access/modify a todo-list
    * subcommands: add, agenda

### Event time specification

Supported in v0.01:

* dateutil.parser.parse()

All of those would eventually be supported in future versions if it's not too difficult to achieve:

* An iso time stamp, followed with the duration, using either + or space as separator.  Duration is a number postfixed by s for seconds, m for minutes, h for hours, d for days, w for weeks and y for years (i.e. 2013-09-10T13:37+30d)
* Two ISO timestamps separated by a dash (-)
* ISO dates without times (default duration will be one day, for two dates full days up to and including the end date is counted)
* "tomorrow" instead of an ISO date
* weekday instead of an ISO date
* clock time without the date; event will be assumed to start within 24 hours.

Alternatively, endtime or duration can be given through options.

Objectives
----------

* It should be really easy and quick to add a todo-list item from the command line.
* It should be really easy and quick to add a calendar item from the command line.
* It should be possible to get out lists ("agenda") of calendar items and todo-items.
* Interface for copying calendar items between calendars, even between calendars on distinct caldav servers

Milestones
----------

* CLI-interface for creating ical calendar events (scheduled for version 0.01)
* CLI-interface for creating ical calendar events (scheduled for version 0.03)
* Config file with CalDAV connection details
* CalDAV login
* Push calendar item into CalDAV server
* Push todo item into CalDAV server

Status
------

2013-09-15: Made a repository at github and wrote up this README.
