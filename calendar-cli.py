#!/usr/bin/python2

## (the icalendar library is not ported to python3?)

import argparse
import pytz
import tzlocal
import time
from datetime import datetime, timedelta, date
import dateutil.parser
from icalendar import Calendar,Event,Todo
import caldav
import uuid
import json
import os
import logging
import sys

__version__ = "0.7"
__author__ = "Tobias Brox"
__author_short__ = "tobixen"
__copyright__ = "Copyright 2013, Tobias Brox"
#__credits__ = []
__license__ = "GPLv3+"
__maintainer__ = "Tobias Brox"
__author_email__ = "t-calendar-cli@tobixen.no"
__status__ = "Development"
__product__ = "calendar-cli"

def _force_datetime(t):
    """
    date objects cannot be compared with timestamp objects, neither in python2 nor python3.  Silly.
    """
    if type(t) == date:
        return datetime(t.year, t.month, t.day)
    else:
        return t

## global constant
## (todo: this doesn't really work out that well, leap seconds/days are not considered, and we're missing the month unit)
time_units = {
    's': 1, 'm': 60, 'h': 3600,
    'd': 86400, 'w': 604800, 'y': 31536000
}

def niy(*args, **kwargs):
    if 'feature' in kwargs:
        raise NotImplementedError("This feature is not implemented yet: %(feature)s" % kwargs)
    raise NotImplementedError

def caldav_connect(args):
    # Create the account
    return caldav.DAVClient(url=args.caldav_url, username=args.caldav_user, password=args.caldav_pass)

def find_calendar(caldav_conn, args):
    if args.calendar_url:
        if '/' in args.calendar_url:
            return caldav.Calendar(client=caldav_conn, url=args.calendar_url)
        else:
            return caldav.Principal(caldav_conn).calendar(name=args.calendar_url)
    else:
        ## Find default calendar
        return caldav.Principal(caldav_conn).calendars()[0]

def _calendar_addics(caldav_conn, ics, uid, args):
    """"
    "Internal" method for adding a calendar object item to the caldav
    server through a PUT.  ASSUMES the ics conforms to rfc4791.txt
    section 4.1 Handles --calendar-url and --icalendar from the args
    """
    if args.icalendar and args.nocaldav:
        print(ics)
        return

    if args.icalendar or args.nocaldav:
        raise ValueError("Nothing to do/invalid option combination for 'calendar add'-mode; either both --icalendar and --nocaldav should be set, or none of them")
        return

    c = find_calendar(caldav_conn, args)
    c.add_event(ics)
 
def calendar_addics(caldav_conn, args):
    """
    Takes an ics from external source and puts it into the calendar.

    From the CalDAV RFC:

    Calendar components in a calendar collection that have different UID
    property values MUST be stored in separate calendar object resources.

    This means the inbound .ics has to be split up into one .ics for
    each event as long as the uid is different.
    """
    if args.file == '-':
        input_ical = sys.stdin.read()
    else:
        with open(args.file, 'r') as f:
            input_ical = f.read()

    c = Calendar.from_ical(input_ical)

    ## unfortunately we need to mess around with the object internals,
    ## since the icalendar library doesn't offer methods out of the
    ## hat for doing such kind of things
    entries = c.subcomponents
    
    ## Timezones should be duplicated into each ics, ref the RFC
    timezones = [x for x in entries if x.name == 'VTIMEZONE']
    
    ## Make a mapping from UID to the other components
    uids = {}
    for x in entries:
        if x.name == 'VTIMEZONE' or not 'UID' in x:
            continue
        uid = x['UID'].to_ical()
        uids[uid] = uids.get(uid, []) + [x]

    for uid in uids:
        c.subcomponents = timezones + uids[uid]
        _calendar_addics(caldav_conn, c.to_ical(), uid, args)

def interactive_config(args, config, remaining_argv):
    import readline
    
    new_config = False
    section = 'default'
    backup = {}
    modified = False
    
    print("Welcome to the interactive calendar configuration mode")
    print("Warning - untested code ahead, raise issues at t-calendar-cli@tobixen.no")
    if not config or not hasattr(config, 'keys'):
        config = {}
        print("No valid existing configuration found")
        new_config = True
    if config:
        print("The following sections have been found: ")
        print("\n".join(config.keys()))
        if args.config_section and args.config_section != 'default':
            section = args.config_section
        else:
            ## TODO: tab completion
            section = raw_input("Chose one of those, or a new name / no name for a new configuration section: ")
        if section in config:
            backup = config[section].copy()
        print("Using section " + section)
    else:
        section = 'default'

    if not section in config:
        config[section] = {}

    for config_key in ('caldav_url', 'caldav_user', 'caldav_pass', 'language', 'timezone'):
        print("Config option %s - old value: %s" % (config_key, config[section].get(config_key, '(None)')))
        value = raw_input("Enter new value (or just enter to keep the old): ")
        if value:
            config[section][config_key] = value
            modified = True

    if not modified:
        print("No configuration changes have been done")
    else:
        options = []
        if section:
            options.append(('save', 'save configuration into section %s' % section))
        if backup or not section:
            options.append(('save_other', 'add this new configuration into a new section in the configuration file'))
        if remaining_argv:
            options.append(('use', 'use this configuration without saving'))
        options.append(('abort', 'abort without saving'))
        print("CONFIGURATION DONE ...")
        for o in options:
            print("Type %s if you want to %s" % o)
        cmd = raw_input("Enter a command: ")
        if cmd in ('save', 'save_other'):
            if cmd == 'save_other':
                new_section = raw_input("New config section name: ")
                config[new_section] = config[section]
                if backup:
                    config[section] = backup
                else:
                    del config[section]
                section = new_section
            if os.path.isfile(args.config_file):
                os.rename(args.config_file, "%s.%s.bak" % (args.config_file, int(time.time())))
            with open(args.config_file, 'w') as outfile:
                json.dump(config, outfile, indent=4)
        

    if args.config_section == 'default' and section != 'default':
        config['default'] = config[section]
    return config
    
def calendar_add(caldav_conn, args):
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    event = Event()
    ## TODO: timezone
    ## read timestamps from arguments
    event_spec = args.event_time.split('+')
    if len(event_spec)>3:
        raise ValueError('Invalid event time "%s" - can max contain 2 plus-signs' % event_time)
    elif len(event_spec)==3:
        event_time = '%s+%s' % tuple(event_spec[0:2])
        event_duration = event_spec[2]
    elif len(event_spec)==2 and not event_spec[1][-1:] in time_units:
        event_time = '%s+%s' % tuple(event_spec[0:2])
        event_duration = '1h'
    elif len(event_spec)==2:
        event_time = '%s' % event_spec[0]
        event_duration = event_spec[1]
    else:
        event_time = event_spec[0]
        event_duration = '1h'
    ## TODO: error handling
    event_duration_secs = int(event_duration[:-1]) * time_units[event_duration[-1:]]
    dtstart = dateutil.parser.parse(event_spec[0])
    event.add('dtstart', dtstart)
    ## TODO: handle duration and end-time as options.  default 3600s by now.
    event.add('dtend', dtstart + timedelta(0,event_duration_secs))
    ## TODO: what does the cryptic comment here really mean, and why was the dtstamp commented out?  dtstamp is required according to the RFC.
    ## not really correct, and it breaks i.e. with google calendar
    event.add('dtstamp', datetime.now())
    ## maybe we should generate some uid?
    uid = uuid.uuid1()
    event.add('uid', str(uid))
    event.add('summary', ' '.join(args.description))
    cal.add_component(event)
    _calendar_addics(caldav_conn, cal.to_ical(), uid, args)
    print("Added event with uid=%s" % uid)

def calendar_delete(caldav_conn, args):
    cal = find_calendar(caldav_conn, args)
    if args.event_uid:
        ## TODO: backwards compatibility hack, and/or caldav API in flux hack.  Should go away at some point.
        if hasattr(cal, 'object_by_uid'):
            event = cal.object_by_uid(args.event_uid)
        else:
            event = cal.event_by_uid(args.event_uid)
    elif args.event_url:
        event = cal.event_by_url(args.event_url)
    elif args.event_timestamp:
        raise NotImplementedError("this hasn't been implemented yet - see code comments")
        ## It seems that at least DAViCal requires the end of the
        ## search to be beyond the event dtend, which makes deletion
        ## by event_timestamp a bit more complex to implement.
        dtstart = dateutil.parser.parse(args.event_timestamp)
        #dtend = dtstart + timedelta(1,0,0,1)
        events = cal.date_search(dtstart, dtend)
        if len(events)>1:
            raise NotImplementedError("Several events found with that timestamp; cowardly refusing to delete anything")
        elif not len(events):
            raise caldav.lib.error.NotFoundError("Couldn't find any event at %s" % dtstart)
        else:
            event = events[0]
    else:
        raise ValueError("Event deletion failed: either uid, url or timestamp is needed")
    event.delete()

def todo_add(caldav_conn, args):
    ## TODO: copied from calendar_add, should probably be consolidated
    if args.icalendar or args.nocaldav:
        niy(feature="add todo item by icalendar raw stdin data or create raw icalendar data to stdout")
    if args.todo_uid:
        uid = args.todo_uid
    else:
        uid = uuid.uuid1()
    if args.top:
        raise ValueError("incompatible option --top to command todo add")
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    todo = Todo()
    ## TODO: what does the cryptic comment here really mean, and why was the dtstamp commented out?  dtstamp is required according to the RFC.
    ## TODO: not really correct, and it breaks i.e. with google calendar
    todo.add('dtstamp', datetime.now())

    for arg in ('due', 'dtstart'):
        if getattr(args, arg):
            if type(getattr(args, arg)) == str:
                val = dateutil.parser.parse(getattr(args, arg))
            else:
                val = getattr(args, arg)
        todo.add(arg, val)
    todo.add('uid', str(uid))
    todo.add('summary', args.description)
    todo.add('status', 'NEEDS-ACTION')
    cal.add_component(todo)
    _calendar_addics(caldav_conn, cal.to_ical(), uid, args)
    print("Added todo item with uid=%s" % uid)

def calendar_agenda(caldav_conn, args):
    if args.nocaldav and args.icalendar:
        niy(feature="Read events from stdin in ical format and list out in prettified format")

    if args.nocaldav:
        raise ValueError("Agenda with --nocaldav only makes sense together with --icalendar")

    if args.from_time:
        dtstart = dateutil.parser.parse(args.from_time)
    else:
        dtstart = datetime.now()
    if args.to_time:
        dtend = dateutil.parser.parse(args.to_time)
    elif args.agenda_mins:
        dtend = dtstart + timedelta(minutes=args.agenda_mins)
    elif args.agenda_days:
        dtend = dtstart + timedelta(args.agenda_days)

    ## TODO: time zone
    events_ = find_calendar(caldav_conn, args).date_search(dtstart, dtend)
    events = []
    if args.icalendar:
        for ical in events_:
            print(ical.data)
    else:
        ## flatten. A recurring event may be a list of events.
        for event_cal in events_:
            for event in event_cal.instance.components():
                dtstart = event.dtstart.value
                if not isinstance(dtstart, datetime):
                    dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
                if not dtstart.tzinfo:
                    dtstart = args.timezone.localize(dtstart)
                events.append({'dtstart': dtstart, 'instance': event})
        events.sort(lambda a,b: cmp(a['dtstart'], b['dtstart']))
        for event in events:
            event['dstart'] = event['dtstart'].strftime(args.timestamp_format)
            for summary_attr in ('summary', 'location'):
                if hasattr(event['instance'], summary_attr):
                    event['description'] = getattr(event['instance'], summary_attr).value
                    break
            event['uid'] = event['instance'].uid.value
            ## TODO: this will probably break and is probably moot on python3?
            if hasattr(event['description'], 'encode'):
                event['description'] = event['description'].encode('utf-8')
            print(args.event_template.format(**event))

def todo_select(caldav_conn, args):
    if args.top and args.todo_uid:
        raise ValueError("It doesn't make sense to combine --todo-uid with --top")
    if args.todo_uid:
        tasks = find_calendar(caldav_conn, args).object_by_uid(args.todo_uid)
    else:
        tasks = find_calendar(caldav_conn, args).todos(sort_keys=('dtstart', 'due', 'priority'))
    if args.top:
        tasks = tasks[0:args.top]
    return tasks

def todo_postpone(caldav_conn, args):
    if args.nocaldav:
        raise ValueError("No caldav connection, aborting")
    rel_skew = None
    new_ts = None
    if args.until.startswith('+'):
        rel_skew = timedelta(seconds=int(args.until[1:-1])*time_units[args.until[-1]])
    elif args.until.startswith('in'):
        new_ts = datetime.now()+timedelta(seconds=int(args.until[2:-1])*time_units[args.until[-1]])
    else:
        new_ts = dateutil.parser.parse(args.until)
        if not new_ts.time():
            new_ts = new_ts.date()
            
    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        if new_ts:
            if not hasattr(task.instance.vtodo, 'dtstart'):
                task.instance.vtodo.add('dtstart')
            task.instance.vtodo.dtstart.value = new_ts
        if rel_skew:
            if hasattr(task.instance.vtodo, 'dtstart'):
                task.instance.vtodo.dtstart.value += rel_skew
            elif hasattr(task.instance.vtodo, 'due'):
                task.instance.vtodo.due.value += rel_skew
            if hasattr(task.instance.vtodo, 'dtstart') and hasattr(task.instance.vtodo, 'due'):
                if type(task.instance.vtodo.dtstart.value) != type(task.instance.vtodo.due.value):
                    ## RFC states they must be of the same type
                    if isinstance(task.instance.vtodo.dtstart.value, date):
                        task.instance.vtodo.due.value = task.instance.vtodo.due.value.date()
                    else:
                        d = task.instance.vtodo.due.value
                        task.instance.vtodo.due.value = datetime(d.year, d.month, d.day)
                    ## RFC also states that due cannot be before dtstart (and that makes sense)
                    if task.instance.vtodo.dtstart.value > task.instance.vtodo.due.value:
                        task.instance.vtodo.due.value = task.instance.vtodo.dtstart.value
        task.save()

def todo_list(caldav_conn, args):
    if args.nocaldav and args.icalendar:
        niy(feature="display a prettified tasklist based on stdin ical")
    if args.nocaldav:
        raise ValueError("Todo-listing with --nocaldav only makes sense together with --icalendar")
    tasks = todo_select(caldav_conn, args)
    if args.icalendar:
        for ical in tasks:
            print(ical.data)
    else:
        for task in tasks:
            t = {'instance': task}
            t['dtstart'] = task.instance.vtodo.dtstart.value if hasattr(task.instance.vtodo,'dtstart') else date.today()
            t['dtstart_passed_mark'] = '!' if _force_datetime(t['dtstart']) <= datetime.now() else ' '
            t['due'] = task.instance.vtodo.dtstart.value if hasattr(task.instance.vtodo,'due') else date.today()+timedelta(365)
            t['due_passed_mark'] = '!' if _force_datetime(t['due']) < datetime.now() else ' '
            for summary_attr in ('summary', 'location', 'description', 'url', 'uid'):
                if hasattr(task.instance.vtodo, summary_attr):
                    t['summary'] = getattr(task.instance.vtodo, summary_attr).value
                    break
            t['uid'] = task.instance.vtodo.uid.value
            ## TODO: this will probably break and is probably moot on python3?
            if hasattr(t['summary'], 'encode'):
                t['summary'] = t['summary'].encode('utf-8')
            print(args.todo_template.format(**t))

def todo_complete(caldav_conn, args):
    if args.nocaldav:
        raise ValueError("No caldav connection, aborting")
    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        task.complete()

def main():
    """
    the main function does (almost) nothing but parsing command line parameters
    """
    ## This boilerplate pattern is from
    ## http://stackoverflow.com/questions/3609852 
    ## We want defaults for the command line options to be fetched from the config file

    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        description=__doc__, # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
        )
    conf_parser.add_argument("--config-file",
                             help="Specify config file", metavar="FILE", default=os.getenv('XDG_CONFIG_HOME', os.getenv('HOME', '~') + '/.config')+'/calendar.conf')
    conf_parser.add_argument("--config-section",
                             help="Specify config section; allows several caldav servers to be configured in the same config file",  default='default')
    conf_parser.add_argument("--interactive-config",
                             help="Interactively ask for configuration", action="store_true")
    args, remaining_argv = conf_parser.parse_known_args()

    config = {}

    try:
        with open(args.config_file) as config_file:
            config = json.load(config_file)
    except IOError:
        ## File not found
        logging.info("no config file found")
    except ValueError:
        if args.interactive_config:
            logging.error("error in config file.  Be aware that the current config file will be ignored and overwritten", exc_info=True)
        else:
            logging.error("error in config file.  You may want to run --interactive-config or fix the config file", exc_info=True)

    if args.interactive_config:
        config = interactive_config(args, config, remaining_argv)
        if not remaining_argv:
            return
    else:
        defaults = config.get(args.config_section, {})

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser]
        )
    parser.set_defaults(**defaults)

    ## Global options
    parser.add_argument("--nocaldav", help="Do not connect to CalDAV server, but read/write icalendar format from stdin/stdout", action="store_true")
    parser.add_argument("--icalendar", help="Read/write icalendar format from stdin/stdout", action="store_true")
    parser.add_argument("--timezone", help="Timezone to use")
    parser.add_argument('--language', help="language used", default="EN")
    parser.add_argument("--caldav-url", help="Full URL to the caldav server", metavar="URL")
    parser.add_argument("--caldav-user", help="username to log into the caldav server", metavar="USER")
    parser.add_argument("--caldav-pass", help="password to log into the caldav server", metavar="PASS")
    parser.add_argument("--debug-logging", help="turn on debug logging", action="store_true")
    parser.add_argument("--calendar-url", help="URL for calendar to be used (may be absolute or relative to caldav URL, or just the name of the calendar)")

    ## TODO: check sys.argv[0] to find command
    ## TODO: set up logging
    subparsers = parser.add_subparsers(title='command')

    ## Tasks
    todo_parser = subparsers.add_parser('todo')
    todo_parser.add_argument('--top', '-1', action='count')
    todo_parser.add_argument('--todo-uid')
    #todo_parser.add_argument('--priority', ....) 
    #todo_parser.add_argument('--sort-by', ....)
    #todo_parser.add_argument('--due-before', ....)
    todo_subparsers = todo_parser.add_subparsers(title='tasks subcommand')
    todo_add_parser = todo_subparsers.add_parser('add')
    todo_add_parser.add_argument('description', nargs='+')
    todo_add_parser.add_argument('--due', default=date.today()+timedelta(7))
    todo_add_parser.add_argument('--dtstart', default=date.today()+timedelta(1))
    todo_add_parser.set_defaults(func=todo_add)
    
    todo_list_parser = todo_subparsers.add_parser('list')
    todo_list_parser.add_argument('--todo-template', help="Template for printing out the event", default="{dtstart}{dtstart_passed_mark} {due}{due_passed_mark} {summary}")
    todo_list_parser.add_argument('--default-due', help="Default number of days from a task is submitted until it's considered due", default=14)
    todo_list_parser.set_defaults(func=todo_list)
    
    todo_postpone_parser = todo_subparsers.add_parser('postpone')
    todo_postpone_parser.add_argument('until', help="either a new date or +interval to add some interval to the existing time, or a @+interval to set the time to a new time relative to the current time.  interval is a number postfixed with a one character unit (any of smhdwy).  If the todo-item has a dstart, this field will be modified, else the due timestamp will be modified.  If both timestamps exists and dstart will be moved beyond the due time, the due time will be set to dtime+duration")
    todo_postpone_parser.set_defaults(func=todo_postpone)

    todo_complete_parser = todo_subparsers.add_parser('complete')
    todo_complete_parser.set_defaults(func=todo_complete)
    
    calendar_parser = subparsers.add_parser('calendar')
    calendar_subparsers = calendar_parser.add_subparsers(title='cal subcommand')
    calendar_add_parser = calendar_subparsers.add_parser('add')
    calendar_add_parser.add_argument('event_time', help="Timestamp and duration of the event.  See the documentation for event_time specifications")
    calendar_add_parser.add_argument('description', nargs='+')
    calendar_add_parser.set_defaults(func=calendar_add)
    calendar_addics_parser = calendar_subparsers.add_parser('addics')
    calendar_addics_parser.add_argument('--file', help="ICS file to upload", default='-')
    calendar_addics_parser.set_defaults(func=calendar_addics)

    calendar_agenda_parser = calendar_subparsers.add_parser('agenda')
    calendar_agenda_parser.add_argument('--from-time', help="Fetch calendar events from this timestamp.  See the documentation for time specifications.  Defaults to now")
    calendar_agenda_parser.add_argument('--to-time', help="Fetch calendar until this timestamp")
    calendar_agenda_parser.add_argument('--agenda-mins', help="Fetch calendar for so many minutes", type=int)
    calendar_agenda_parser.add_argument('--agenda-days', help="Fetch calendar for so many days", type=int, default=7)
    calendar_agenda_parser.add_argument('--event-template', help="Template for printing out the event", default="{dstart} {description}")
    calendar_agenda_parser.add_argument('--timestamp-format', help="strftime-style format string for the output timestamps", default="%F %H:%M (%a)")
    calendar_agenda_parser.set_defaults(func=calendar_agenda)

    calendar_delete_parser = calendar_subparsers.add_parser('delete')
    calendar_delete_parser.add_argument('--event-uid')
    calendar_delete_parser.add_argument('--event-url')
    calendar_delete_parser.add_argument('--event-timestamp')
    calendar_delete_parser.set_defaults(func=calendar_delete)

    args = parser.parse_args(remaining_argv)

    if args.timezone:
        args.timezone = pytz.timezone(args.timezone)
    else:
        args.timezone = tzlocal.get_localzone()
        
    if not args.nocaldav:
        caldav_conn = caldav_connect(args)

    ret = args.func(caldav_conn, args)

if __name__ == '__main__':
    main()
