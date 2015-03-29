calendar-cli
============

Simple command-line CalDav client, for adding and browsing calendar items, todo list items, etc

There is a "competing" project at https://github.com/geier/khal - you may want to check it out - it's more mature but probably more complex.  It's using a "vsyncdir" backend - if I've understood it correctly, that involves building a local copy of the calendar.  The philosophy behind calendar-cli is slightly different, calendar-cli is supposed to be a simple cli-based caldav+ical client.  No synchronization, no local storage.

Support
-------

\#calendar-cli at irc.freenode.org, eventually t-calendar-cli@tobixen.no, eventually the issue tracker at https://github.com/tobixen/calendar-cli/issues

Status
------

This is work in progress.  Writing to calendars seems to work, and I'm using it actively for adding stuff to my calendars - taking out the agenda is also possible, but could need more work.

This is written in python2 as some of the libraries being used aren't
available in python3.

Rationale
---------

GUIs and Web-UIs are nice for some purposes, but I really find the command line unbeatable when it comes to:

* Minor stuff that are repeated often.  Writing something like "todo add make a calendar-cli system" or "cal add 'tomorrow 15:40+2h' doctor appointment" is just very much faster than navigating into some web calendar interface and add an item there.
* Things that are outside the scope of the UI.  Here is one of many tasks I'd like to do: "go through the work calendar, find all new calendar events that are outside office hours, check up with the personal calendar if there are potential conflicts, add some information at the personal calendar if appropriate", and vice versa - it has to be handled very manually if doing it through any normal calendar application as far as I know, but if having some simple CLI or python library I could easily make some interactive script that would help me doing the operation above.

I've been looking a bit around, all I could find was cadaver and CalDAVClientLibrary.  Both of those seems to be a bit shortcoming; they seem to miss the iCalendar parsing/generation.  CalDAVClientLibrary is already a python library, and there also exist python libraries for iCalendar parsing/generation, so all that seems to be missing is the "glue" between those libraries.  Or, eventually, not.  After some problems I decided to ditch CalDAVClientLibrary.

Synopsis
--------

    calendar-cli.py [global options] [command] [command options] [subcommand] [subcommand options] [subcommand arguments] ...

I'm intending to make it easier by allowing calendar-cli.py to be symlinked to the various commands.

### Global options

Only long options will be available up until version 0.10; I don't
want to pollute the short option space before the CLI is reasonably
well-defined.

Always consult --help for up-to-date and complete listings of options.
The list below will only contain the most important options and may
not be up-to-date and may contain features not implemented yet.

* --interactive: stop and query the user rather often
* --caldav-url, --caldav-user, --caldav-pass: how to connect to the CalDAV server.  Fits better into a configuration file.
* --config-file: use a specific configuration file (default: $HOME/.calendar-cli.conf)
* --config-section: use a specific section from the config file (i.e. to select a different caldav-server to connect to)
* --icalendar: Write or read icalendar to/from stdout/stdin
* --nocaldav: don't connect to a caldav server

### Commands

* cal - access/modify a calendar
    * subcommands: add, addics (for uploading events in ical format), agenda
* todo - access/modify a todo-list
    * subcommands: add, agenda

(only "cal add" and "cal addics" works as of v0.06 / 2013-12-02)

### Event time specification

Supported in v0.06:

* anything recognized by dateutil.parser.parse()

All of those would eventually be supported in future versions if it's not too difficult to achieve:

* An iso time stamp, followed with the duration, using either + or space as separator.  Duration is a number postfixed by s for seconds, m for minutes, h for hours, d for days, w for weeks and y for years (i.e. 2013-09-10T13:37+30d)
* Two ISO timestamps separated by a dash (-)
* ISO dates without times (default duration will be one day, for two dates full days up to and including the end date is counted)
* "tomorrow" instead of an ISO date
* weekday instead of an ISO date
* clock time without the date; event will be assumed to start within 24 hours.

Alternatively, endtime or duration can be given through options (not supported as of 0.06.  All events are considered to be one hour long).

Configuration file
------------------

Configuration file is by default located in $HOME/.config/calendar.conf and should be in json syntax.  As of version 0.8 you may run `calendar-cli --interactive-config` if you don't feel comfortable with hand-crafting configuration in json syntax.

(I considered a configuration file in .ini-format, having a "default"-section with default values for any global options, and optionally other sections for different CalDAV-servers.  Asking a bit around for recommendations on config file format as well as location, I was told that the .ini-format is not a standard, I'd be better off using a standard like yaml, json or xml.  Personally I like json a bit better than yaml - after consulting with a friend I ended up with json.  Location ... I think it's "cleaner" to keep it in ~/.config/, and I'd like any calendar application to be able to access the file, hence it got ~/.config/calendar.conf rather than ~/.calendar-cli.conf)

The file may look like this:

```json
{ "default": 
  { "caldav_url": "http://foo.bar.example.com/caldav/", 
    "caldav-user": "luser",
    "caldav-pass": "insecure"
  }
}
```

Optionally, in addition (or even instead) of "default", other "sections" can be created and selected through the --config-section option.  The rationale is to allow configuration for multiple CalDAV-servers to remain in the same configuration file.  Later versions will eventually be capable of copying events, or putting events into several calendars.

Remember to `chmod og-r ~/.config/calendar.conf` or `chmod 0600 ~/.config/calendar.conf`

### Examples

Add a calendar item "testevent" at 2013-10-01:

    ./calendar-cli.py calendar --calendar-url=http://calendar.bekkenstenveien53c.oslo.no/caldav.php/tobias/calendar/ add 2013-10-01 testevent

(assumes that `caldav-url`, `calldav-pass` and `caldav-user` has been added into configuration file.  Those may also be added as command line options)

Objectives
----------

* It should be really easy and quick to add a todo-list item from the command line.
* It should be really easy and quick to add a calendar item from the command line.
* It should be possible to get out lists ("agenda") of calendar items and todo-items.
* Interface for copying calendar items between calendars, even between calendars on distinct caldav servers

Status
------

2013-09-15: Made a repository at github and wrote up this README.
2013-09-24: version 0.01 - supports creating an ical-file based on command line parameters
2013-09-28: version 0.02 - possible to add a calendar item to the caldav server
2013-10-02: version 0.03 - support for configuration file
2013-10-05: version 0.04 - no need to specify URL for the default calendar
2013-12 - 2014-03: helped cyrilrbt on making a new release of the caldav library
2014-03-07: version 0.05 - rewrote parts of the tool to using the caldav library.  Nice!!!
2014-03-14: version 0.6 - now agenda works quite smooth.  I think this is becoming a useful tool.
2015-02-15: version 0.7 - supports deletion of events, alternative templates for the event output and a small testing script
2015-03-30: version 0.8 - has a interactive configuration mode for those not feeling comfortable with hand-crafting the config in json syntax

Roadmap
-------
* Allow specification of event duration when adding events to calendar
* CLI-interface for creating ical todo events
* Fix easy-to-use symlinks (or alternatively wrapper scripts)
* Make some nosetests
