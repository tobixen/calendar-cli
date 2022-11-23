# User guide for calendar-cli v1.0

The `kal` command is under heavy development, this document may not always be up-to-date.  As of 2022-11, `kal` can do nearly all the things the old command `calendar-cli` can do.  In the upcoming release 1.0 one is supposed to use `kal`, with `calendar-cli` being a deprecated legacy interface retained only for backward-compatibility.

## Command structure

Commands are on this format:

```bash
kal --global-options command --command-options subcommand --subcommand-options
```

The most up-to-date documentation can always be found through `--help`, and it's outside the scope of this document to list all the options.

```bash
kal --help
kal command --help
kal command subcommand --help
```

## Main commands

* test - verify that it's possible to connect to the server
* add - for adding things to the calendar(s)
* select - for selecting, viewing, editing and deleting things from the calendar(s).

## Global options

The global options are for setting the connection parameters to the server and choosing what calendar(s) to operate at.  Connection parameters may be typed in directly:

* `--caldav-*` to set the server connection parameters
* `--calendar-*` to choose a calendar.  If nothing is specified, the first calendar found will be utilized (on some calendar servers, this will be the default calendar).  It's possible to specify those parameters multiple times.

It's recommended to rather use a config file (though not yet supported as of 2022-10-09).  Those options can be used for specifying a config file:

* `--config-file`
* `--config-section`

The default (though not yet supported as of 2022-10-09) is to utilize the `default` section under `$HOME/.config/calendar.conf`

Multiple config sections can be specified, which may be useful for selecting things from multiple calendars.

## Adding things to the calendar

Generally it should be done like this:

```
kal add ical --ical-file=some_calendar_data.ics
kal add event --event-options 'New years party' '2022-12-31T17:00+8h'
kal add todo --todo-options 'Prepare for the new years party'
kal add journal --journal-options "Resume from the new years party" 2022-12-31 "It was awesome.  Lots of delicous food and drinks.  Lots of firework."
```

(journals not supported yet as of 2022-10-09)

Most often, no options should be given to the command `add` - with the exception if one wants to add things to multiple calendars in one command.

Most of the options given after the subcommand is for populating object properties like location, categories, geo, class, etc.

## Selecting things from the calendar

```
kal select --selection-parameters select-command
```

It's usually a good idea to start with the select-command `list`, for instance:

```
kal select --todo --category computer-work list
```

Some calendar server implementations require  `--todo` or `--event` to always be given when doing selects, others not.

### Listing objects

Events can either be output as ics, or through a template.

The templating engine is built on top of the python `string.format()`.  To learn the basics of `string.format()`, w3schools have some nice interactive thing on the web, https://www.w3schools.com/python/ref_string_format.asp

Text fields can be accessed directly i.e. like this:

```
kal select --todo list --template='{SUMMARY} {DESCRIPTION} {LOCATION}'
```

Dates can be accessed through the dt property, and can be formatted using strftime format, like this:

```
kal select --event list --template='{DTSTART.dt:%F %H:%M:%S}: {SUMMARY}'
```

If a property is missing, the default is to insert an empty string - but it's also possible to put a default value like this:

```
kal select --event list --template='{DTSTART.dt:%F %H:%M:%S}: {SUMMARY:?(no summary given)?}'
```

It's even possible to make compounded defaults, like this:

```
kal select --todo list --template='{DUE:?{DTSTART.dt:?(Best effort)?}?:%F %H:%M:%S}: {SUMMARY:?(no summary given)?}'
```

One thing that may be particularly useful is to take out the UID fields.  With UID one can be sure to delete exactly the right row:

```
kal select --todo list --template='{UID} {SUMMARY}'
```

### Printing a UID

The subcommand `print-uid` will print out an UID.  It's for convenience, the same can be achieved by doing a `select (...) --limit 1 list --template='{UID}'`

### Editing and deleting objects

```
kal select --todo --uid=1234-5678-9abc delete
kal select --todo --category computer-work --start=2022-04-04 --end=2022-05-05 edit --complete ## not supported yet
kal select --todo --category computer-work --overdue edit --postpone=5d ## not supported yet

## See also

[NEW_CLI.md](NEW_CLI.md) is a longer, but possibly less up-to-date document containing some visions of the new `kal`-command.
[NEXT_LEVEL.md](NEXT_LEVEL.md) describes some of my visions on what a good calendaring system should be capable of, and does an attempt on mapping this down to the icalendar standard.
