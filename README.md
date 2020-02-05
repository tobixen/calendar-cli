calendar-cli
============

Simple command-line CalDav client, for adding and browsing calendar items, todo list items, etc.  As of version 0.11 it's even becoming a full-fledged task management tool.

Other tools
-----------

There is another project out there, "Command-line Interface for Google Calendar", previously located at pypi under the calendar-cli name.  It has now been renamed to gcalendar-cli to avoid name conflict, and is available at https://pypi.python.org/pypi/gcalendar-cli/

There is a "competing" project at https://github.com/geier/khal - you may want to check it out - it's more mature but probably more complex.  It's using a "vsyncdir" backend - if I've understood it correctly, that involves building a local copy of the calendar.  The philosophy behind calendar-cli is slightly different, calendar-cli is supposed to be a simple cli-based caldav+ical client.  No synchronization, no local storage.


Support
-------

\#calendar-cli at irc.freenode.org, eventually t-calendar-cli@tobixen.no, eventually the issue tracker at https://github.com/tobixen/calendar-cli/issues

Rationale
---------

GUIs and Web-UIs are nice for some purposes, but I really find the command line unbeatable when it comes to:

* Minor stuff that are repeated often.  Writing something like "todo add make a calendar-cli system" or "calendar add 'tomorrow 15:40+2h' doctor appointment" is just very much faster than navigating into some web calendar interface and add an item there.
* Things that are outside the scope of the UI.  Here is one of many tasks I'd like to do: "go through the work calendar, find all new calendar events that are outside office hours, check up with the personal calendar if there are potential conflicts, add some information at the personal calendar if appropriate", and vice versa - it has to be handled very manually if doing it through any normal calendar application as far as I know, but if having some simple CLI or python library I could easily make some interactive script that would help me doing the operation above.

I've been looking a bit around, all I could find was cadaver and CalDAVClientLibrary.  Both of those seems to be a bit shortcoming; they seem to miss the iCalendar parsing/generation, and there are things that simply cannot be done through those tools.

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
* --calendar-url: url to the calendar one wants to use.
* --config-file: use a specific configuration file (default: $HOME/.config/calendar.conf)
* --config-section: use a specific section from the config file (i.e. to select a different caldav-server to connect to)
* --icalendar: Write or read icalendar to/from stdout/stdin
* --nocaldav: don't connect to a caldav server

The caldav URL is supposed to be something like i.e. http://some.davical.server/caldav.php/ - it is only supposed to relay the server location, not the user or calendar.  It's a common mistake to use something like http://some.davical.server/caldav.php/tobixen/work-calendar/ - it will also work, but it will ignore the calendar part of it, and use first calendar it can find - perhaps tobixen/family-calendar/.  Use http://some.davical.server/caldav.php/ as the caldav URL, and tobixen/family-calendar as the calendar-url.

### Commands

* calendar - access/modify a calendar
    * subcommands: add, addics (for uploading events in ical format), agenda, delete
* todo - access/modify a todo-list
    * subcommands: add, list, edit, postpone, complete, delete

### Event time specification

Supported in v0.8:

* anything recognized by dateutil.parser.parse()
* An iso time stamp, followed with the duration, using either + or space as separator.  Duration is a number postfixed by s for seconds, m for minutes, h for hours, d for days, w for weeks and y for years (i.e. 2013-09-10T13:37+30d)

All of those would eventually be supported in future versions if it's not too difficult to achieve:

* Two ISO timestamps separated by a dash (-)
* ISO dates without times (default duration will be one day, for two dates full days up to and including the end date is counted)
* "tomorrow" instead of an ISO date
* weekday instead of an ISO date (this seems supported already by dateutil.parser.parse)
* clock time without the date; event will be assumed to start within 24 hours.

Alternatively, endtime or duration can be given through options (not supported as of 0.9)

Configuration file
------------------

Configuration file is by default located in $HOME/.config/calendar.conf and should be in json syntax.  As of version 0.8 you may run `calendar-cli --interactive-config` if you don't feel comfortable with hand-crafting configuration in json syntax.

(I considered a configuration file in .ini-format, having a "default"-section with default values for any global options, and optionally other sections for different CalDAV-servers.  Asking a bit around for recommendations on config file format as well as location, I was told that the .ini-format is not a standard, I'd be better off using a standard like yaml, json or xml.  Personally I like json a bit better than yaml - after consulting with a friend I ended up with json.  Location ... I think it's "cleaner" to keep it in ~/.config/, and I'd like any calendar application to be able to access the file, hence it got ~/.config/calendar.conf rather than ~/.calendar-cli.conf)

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
{ "default":
  { "caldav_url": "http://foo.bar.example.com/caldav/",
    "caldav_user": "luser",
    "caldav_pass": "insecure"
  },
  "caldav_url": "http://foo.baz.example.com/caldav/",
    "caldav_user": "luser2",
    "caldav_pass": "insecure2"
  }
}
```

Optionally, in addition (or even instead) of "default", other "sections" can be created and selected through the --config-section option.  The rationale is to allow configuration for multiple CalDAV-servers, or multiple calendars on the same CalDAV-server to remain in the same configuration file.  Later versions will eventually be capable of copying events, or putting events into several calendars.

Remember to `chmod og-r ~/.config/calendar.conf` or `chmod 0600 ~/.config/calendar.conf`

### Examples

Add a calendar item "testevent" at 2013-10-01:

    ./calendar-cli.py --calendar-url=http://calendar.bekkenstenveien53c.oslo.no/caldav.php/tobias/calendar/ calendar add 2013-10-01 testevent

(assumes that `caldav-url`, `calldav-pass` and `caldav-user` has been added into configuration file.  Those may also be added as command line options)

Objectives
----------

* It should be really easy and quick to add a todo-list item from the command line.
* It should be really easy and quick to add a calendar item from the command line.
* It should be possible to get out lists ("agenda") of calendar items and todo-items.
* Interface for copying calendar items between calendars, even between calendars on distinct caldav servers

Roadmap
-------
This is being moved out to the issues section in github.

* Allow pulling out an agenda for all calendars at once (though, with the current design it's so much easier to do it through a bash loop rather than in the python code, so this is postponed for a while)
* Allow specification of event duration and/or event end time through options
* Fix easy-to-use symlinks (or alternatively wrapper scripts)
* Make some nosetests
