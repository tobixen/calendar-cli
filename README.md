calendar-cli
============

Simple command-line CalDAV client, making it possible to add calendar events, browse an agenda and do task management using a caldav server.

THIS IS THE LEGACY VERSION.  I decided to change a bit on the user interface, rather than breaking backward compatibility I made a new command name `plann`.  Please visit https://github.com/tobixen/plann for the new version (though be aware that it still has some sharp edges).

calendar-cli will be maintained primarily for backward compatibility.  Pull-requests dealing with bugfixes or minor "missing" features will be considered - but for anyone in need of a command-line interface towards a CalDAV calendar server, the recommendation is to use [plann](https://github.com/tobixen/plann) instead.

Other tools
-----------

There is another project out there, "Command-line Interface for Google Calendar", previously located at pypi under the calendar-cli name.  It has now been renamed to gcalendar-cli to avoid name conflict, and is available at https://pypi.python.org/pypi/gcalendar-cli/

There is a "competing" project at https://github.com/geier/khal - you may want to check it out - it's more mature but probably more complex.  It's using a "vsyncdir" backend - if I've understood it correctly, that involves building a local copy of the calendar.  The philosophy behind `calendar-cli` is slightly different, `calendar-cli` is supposed to be a simple cli-based caldav+ical client.  No synchronization, no local storage, just client-side operations.

New vs old interface
--------------------

DO YOU HAVE OPINIONS ON WHAT COLOR TO PAINT THE BIKE SHED WITH?  VISIT https://github.com/tobixen/calendar-cli/issues/88 NOW!

calendar-cli.py is the old interface, it will hang around and be supported for some time to come.  cal.py is the new interface, but until version 1.0 is ready, there will still be functionality in calendar-cli that isn't mirrored to cal.py.

Usage examples
--------------

The commands and options will be described further down, however examples often beat documentation.

First, check the tests folder - the file tests.sh shows some basic usage examples.  If you have radicale installed (`sudo pip install radicale`), you can try executing test_calendar-cli.sh in the test folder, it basically sets up a temporary radicale server and executes the tests.sh towards that server.  If test_calendar-cli.sh breaks then _please_ raise an issue on the github or try to reach out through other channels.

In the examples folder there is a script I was using on a regular basis for task management for a while.

Installation
------------

`calendar-cli` depends on quite some python libraries, i.e. pytz, caldav, etc.  "sudo ./setup.py install" should take care of all those eventually, and will also make an executable under /usr/bin

Support
-------

\#calendar-cli at irc.oftc.net, eventually t-calendar-cli@tobixen.no, eventually the issue tracker at https://github.com/tobixen/calendar-cli/issues

Before reaching out, please make sure all the dependencies are installed and that you've installed the latest version of the caldav python library.

Rationale
---------

GUIs and Web-UIs are nice for some purposes, but I really find the command line unbeatable when it comes to:

* Minor stuff that is repeated often.  Writing something like "todo add make a calendar-cli system" or "calendar add 'tomorrow 15:40+2h' doctor appointment" is (for me) faster than navigating into some web calendar interface and add an item there.
* Things that are outside the scope of the UI.  Here is one of many tasks I'd like to do: "go through the work calendar, find all new calendar events that are outside office hours, check up with the personal calendar if there are potential conflicts, add some information at the personal calendar if appropriate", and vice versa - it has to be handled very manually if doing it through any normal calendar application as far as I know, but if having some simple CLI or python library I could easily make some interactive script that would help me doing the operation above.

When I started writing `calendar-cli`, all I could find was cadaver and the CalDAVClientLibrary.  Both of those seems to be a bit shortcoming; they seem to miss the iCalendar parsing/generation, and there are things that simply cannot be done through those tools.

Synopsis
--------

    calendar-cli.py [global options] [command] [command options] [subcommand] [subcommand options] [subcommand arguments] ...

I'm intending to make it easier by allowing calendar-cli.py to be symlinked to the various commands and also to allow the options to be placed wherever.

### Global options

Only long options will be available in the early versions; I don't
want to pollute the short option space before the CLI is reasonably
well-defined.

Always consult --help for up-to-date and complete listings of options.
The list below will only contain the most important options and may
not be up-to-date and may contain features not implemented yet.

* --interactive: stop and query the user rather often
* --caldav-url, --caldav-user, --caldav-pass: how to connect to the CalDAV server.  Fits better into a configuration file.
* --calendar-url: url to the calendar one wants to use.  A relative URL (path) or a calendar-id is also accepted.
* --config-file: use a specific configuration file (default: $HOME/.config/calendar.conf)
* --config-section: use a specific section from the config file (i.e. to select a different caldav-server to connect to)
* --icalendar: Write or read icalendar to/from stdout/stdin
* --nocaldav: don't connect to a caldav server
* --timezone: any "naive" timestamp should be considered to belong to the given time zone, timestamps outputted should be in this time zone, timestamps given through options should be considered to be in this time zone (Olson database identifiers, like UTC or Europe/Helsinki). (default: local timezone)

The caldav URL is supposed to be something like i.e. http://some.davical.server/caldav.php/ - it is only supposed to relay the server location, not the user or calendar.  Things will most likely work if you give http://some.davical.server/caldav.php/tobixen/work-calendar/ - but it will ignore the calendar part of it, and use first calendar it can find - which perhaps may be tobixen/family-calendar/.  Use http://some.davical.server/caldav.php/ as the caldav URL, and /tobixen/family-calendar as the calendar-url.

### Commands

As of 0.12, there are two or three distinct commands - calendar (for management of events) and todo (for task management), with quite different code paths.  The third thing is journal ... but as far as I know, it's not much common to use caldav servers for keeping journals, the journal thing is not much tested nor much rich on features.

There will be code refactorings in v1.0, applying quite some of the logic in the task management to the calendar management.

* calendar - access/modify a calendar
    * subcommands: add, addics (for uploading events in ical format), agenda, delete, create (for creating a new calendar)
* todo - access/modify a todo-list
    * subcommands: add, list, edit, postpone, complete, delete, addlist

todo addlist: for creating a new task list.  Most caldav servers don't make any difference between a task list and a calendar.  Zimbra is an exception.  addlist hasn't been tested as of version 0.12, perhaps it works, perhaps not)

### Event time specification

Supported in v0.12:

* anything recognized by dateutil.parser.parse()
* An iso time stamp, followed with the duration, using either + or space as separator.  Duration is a number postfixed by s for seconds, m for minutes, h for hours, d for days, w for weeks and y for years (i.e. 2013-09-10T13:37+30d)
* ISO dates.  For full day events, make sure to specify the duration in days.

All of these would eventually be supported in future versions if it's not too difficult to achieve:

* Two ISO timestamps separated by a dash (-)
* "tomorrow" instead of an ISO date
* weekday instead of an ISO date (this seems supported already by dateutil.parser.parse)
* clock time without the date; event will be assumed to start within 24 hours.

Alternatively, endtime or duration can be given through options (not supported as of 0.12)

### Getting out customized information through --todo-template and --event-template

This is a string containing variables enclosed in curly braces, like "uid: {uid}".  Full documentation of the available variables will be given in version 1.0.

Particularly the uid can be useful, as one may want to use the uid for things like deleting events and postponing tasks.

In the examples folder there is a task management script which will use the --todo-template to create a new shell script for postponing all overdue tasks.  This shell script can then be edited interactively and run.

### Task management

With the todo-command, there are quite some options available (i.e. --categories, --limit, --todo-uid, etc) to select or filter tasks.  Those are used by the commands list, edit, postpone, complete and delete.  A typical use-case scenario is to first use the "list" command, tweak the filtering options to get a list containing the tasks one wants to operate with, and then use either edit, postpone, complete or delete.

The file TASK_MANAGEMENT.md contains some thoughts on how to organize tasks.

Configuration file
------------------

Configuration file is by default located in $HOME/.config/calendar.conf. You may run `calendar-cli --interactive-config` if you don't feel comfortable with hand-crafting configuration in json syntax, though this feature is not tested regularly.

(I considered .ini, but I was told that it's actually not a standard.  I'd like any calendar application to be able to access the file, hence calendar.conf and not calendar-cli.conf)

### calendar-cli

The file may look like this:

```json
{ "default":
  { "caldav_url": "http://foo.bar.example.com/caldav/",
    "caldav_user": "luser",
    "caldav_pass": "insecure"
  }
}
```
A configuration with multiple sections may look like this:

```json
{
"default":
  { "caldav_url": "http://foo.bar.example.com/caldav/",
    "caldav_user": "luser",
    "caldav_pass": "insecure"
  },
"baz":
  { "caldav_url": "http://foo.baz.example.com/caldav/",
    "caldav_user": "luser2",
    "caldav_pass": "insecure2"
  }
}
```

Sections may also include calendar urls or ids, and sections may inherit other sections:

```json
{
"default":
  { "caldav_url": "http://foo.bar.example.com/caldav/",
    "caldav_user": "luser",
    "caldav_pass": "insecure"
  },
"baz":
  { "caldav_url": "http://foo.baz.example.com/caldav/",
    "caldav_user": "luser2",
    "caldav_pass": "insecure2"
  }
},
"bazimportant":
  { "inherits": "baz",
    "calendar_url": "important"
  }
```

Usage example
-------------

Add a calendar item "testevent" at 2013-10-01:

    ./calendar-cli.py --calendar-url=http://calendar.bekkenstenveien53c.oslo.no/caldav.php/tobias/calendar/ calendar add 2013-10-01 testevent

(assumes that `caldav-url`, `caldav-pass` and `caldav-user` has been added into configuration file.  Those may also be added as command line options)

Objectives
----------

* It should be really easy and quick to add a todo-list item from the command line.
* It should be really easy and quick to add a calendar item from the command line.
* It should be possible to get out lists ("agenda") of calendar items and todo-items.
* Interface for copying calendar items between calendars, even between calendars on distinct caldav servers

Roadmap
-------

See https://github.com/tobixen/plann for the direction the project is heading.
