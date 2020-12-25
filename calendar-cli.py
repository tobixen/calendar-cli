#!/usr/bin/env python

"""
https://github.com/tobixen/calendar-cli/ - high-level cli against caldav servers.

Copyright (C) 2013-2020 Tobias Brox and other contributors.

See https://www.gnu.org/licenses/gpl-3.0.en.html for license information.
"""

import argparse
import pytz
import tzlocal
import time
from datetime import datetime, timedelta, date
from datetime import time as time_
import dateutil.parser
from dateutil.rrule import rrulestr
from icalendar import Calendar,Event,Todo,Journal,Alarm
import vobject
import caldav
import uuid
import json
import os
import logging
import sys
import re
import urllib3
from getpass import getpass
from six import PY3

def to_normal_str(text):
    if PY3 and text and not isinstance(text, str):
        text = text.decode('utf-8')
    elif not PY3 and text and not isinstance(text, str):
        text = text.encode('utf-8')
    return text


## ref https://github.com/tobixen/calendar-cli/issues/33, python3-compatibility
try:
    raw_input
except NameError:
    raw_input = input

try:
    unicode
except NameError:
    unicode = str

__version__ = "0.12.0"
__author__ = "Tobias Brox"
__author_short__ = "tobixen"
__copyright__ = "Copyright 2013-2020, Tobias Brox"
#__credits__ = []
__license__ = "GPLv3+"
__license_url__ = "http://www.gnu.org/licenses/gpl-3.0-standalone.html"
__maintainer__ = "Tobias Brox"
__author_email__ = "t-calendar-cli@tobixen.no"
__status__ = "Development"
__product__ = "calendar-cli"
__description__ = "high-level cli against caldav servers"

def _date(ts):
    """
    helper function to get a date out of a Date or Datetime object.
    """
    if hasattr(ts, 'date'):
        return ts.date()
    return ts

def _force_datetime(t, args):
    """
    date objects cannot be compared with timestamp objects, neither in
    python2 nor python3.  Silly.  also, objects with time zone info
    cannot be compared with timestamps without time zone info.  and
    both datetime.now() and datetime.utcnow() seems to be without
    those bits.  Silly.

    This method should only be used in comparitions, never when
    populating fields in an icalendar object.  Events with dates
    rather than timestamps are to be considered as full-day events,
    so the difference is significant.
    """
    if type(t) == date:
        t = datetime(t.year, t.month, t.day)
    if t.tzinfo is None:
        return t.replace(tzinfo=_tz(args.timezone))
    return t

def _now():
    """
    python datetime is ... crap!
    """
    return datetime.utcnow().replace(tzinfo=pytz.utc)

def _tz(timezone=None):
    if timezone:
        return pytz.timezone(timezone)
    else:
        return tzlocal.get_localzone()


## global constant
## (todo: this doesn't really work out that well, leap seconds/days are not considered, and we're missing the month unit)
## (todo: Sebastian Brox has made some other code using regexps and dateutil.relativedelta, should consider to steal his code)
time_units = {
    's': 1, 'm': 60, 'h': 3600,
    'd': 86400, 'w': 604800, 'y': 31536000
}

vtodo_txt_one = ['location', 'description', 'geo', 'organizer', 'summary']
vtodo_txt_many = ['categories', 'comment', 'contact', 'resources']
vcal_txt_one = ['location', 'description']
vcal_txt_many = []

def niy(*args, **kwargs):
    if 'feature' in kwargs:
        raise NotImplementedError("This feature is not implemented yet: %(feature)s" % kwargs)
    raise NotImplementedError

def caldav_connect(args):
    ## args.ssl_verify_cert is a string and can be a path or 'yes'/'no'.
    ## the library expects a path or a boolean.
    ## Translate 'yes' and 'no' to True and False, or pass the raw string:
    ssl_verify_cert = {
        'yes': True,
        'no': False
    }.get(args.ssl_verify_cert, args.ssl_verify_cert)
    # Create the account
    return caldav.DAVClient(url=args.caldav_url, username=args.caldav_user, password=args.caldav_pass, ssl_verify_cert=ssl_verify_cert, proxy=args.caldav_proxy)

def parse_time_delta(delta_string):
    # TODO: handle bad strings more gracefully
    if len(delta_string) < 2 or delta_string[-1].lower() not in time_units:
        raise ValueError("Invalid time delta: %s" % delta_string)
    num = int(delta_string[:-1])
    return timedelta(0, num*time_units[delta_string[-1].lower()])

def find_calendar(caldav_conn, args):
    if args.calendar_url:
        if '/' in args.calendar_url:
            return caldav.Calendar(client=caldav_conn, url=args.calendar_url)
        else:
            return caldav.Principal(caldav_conn).calendar(cal_id=args.calendar_url)
    else:
        ## Find default calendar
        calendars = caldav.Principal(caldav_conn).calendars()
        if not calendars:
            sys.stderr.write("no calendar url given and no default calendar found - can't proceed.  You will need to create a calendar first")
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

    try:
        c = find_calendar(caldav_conn, args)
        ## unicode strings vs byte strings is a minefield in python3 ... so, re.search demands a string here ...
        ics = to_normal_str(ics)
        if re.search(r'^METHOD:[A-Z]+[\r\n]+',ics,flags=re.MULTILINE) and args.ignoremethod:
            ics = re.sub(r'^METHOD:[A-Z]+[\r\n]+', '', ics, flags=re.MULTILINE)
            print ("METHOD property found and ignored")
        c.add_event(ics)
    except caldav.lib.error.AuthorizationError:
        print("Error logging in")
        sys.exit(2)
    """
    Peter Havekes: This needs more checking. It works for me when connecting to O365
    
    except caldav.lib.error.PutError as e:
        if "200 OK" in str(e):
            print("Duplicate")
        else:
            raise
    """

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
    print("Warning - untested code ahead, raise issues at t-calendar-cli@tobixen.no or the github issue tracker")
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

    for config_key in ('caldav_url', 'caldav_user', 'caldav_pass', 'caldav_proxy', 'ssl_verify_cert', 'language', 'timezone', 'inherits'):

        if config_key == 'caldav_pass':
            print("Config option caldav_pass - old value: **HIDDEN**")
            value = getpass(prompt="Enter new value (or just enter to keep the old): ")
        else:
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

def create_alarm(message, relative_timedelta):
    alarm = Alarm()
    alarm.add('ACTION', 'DISPLAY')
    alarm.add('DESCRIPTION', message)
    alarm.add('TRIGGER', relative_timedelta, parameters={'VALUE':'DURATION'})
    return alarm

def calendar_add(caldav_conn, args):
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    event = Event()
    ## read timestamps from arguments
    event_spec = args.event_time.split('+')
    if len(event_spec)>3:
        raise ValueError('Invalid event time "%s" - can max contain 2 plus-signs' % args.event_time)
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
    dtstart = dateutil.parser.parse(event_spec[0], ignoretz=True)
    if (args.whole_day or
        (event_duration_secs % (60*60*24) == 0 and
         dtstart.time() == time_(0,0))):
        
        ## allowing 1 second off due to leap seconds
        if (event_duration_secs+1) % (60*60*24) > 2:
            raise ValueError('Duration of whole-day event must be multiple of 1d')
        
        duration = event_duration_secs//60//60//24
        dtend = dtstart + timedelta(days=duration)
        event.add('dtstart', _date(dtstart.date()))
        event.add('dtend', _date(dtend.date()))
    else:
        dtstart = _tz(args.timezone).localize(dtstart)
        event.add('dtstart', dtstart)
        ## TODO: handle duration and end-time as options.  default 3600s by now.
        event.add('dtend', dtstart + timedelta(0,event_duration_secs))
    if (args.private):
        event.add('class', 'PRIVATE')
    event.add('dtstamp', _now())
    uid = uuid.uuid1()
    event.add('uid', str(uid))
    for attr in vcal_txt_one + vcal_txt_many:
        if attr == 'summary':
            continue
        val = getattr(args, 'set_'+attr)
        if val:
            event.add(attr, val)
    event.add('summary', ' '.join(args.summary))
    cal.add_component(event)
    ## workaround for getting RFC-compliant ical data,
    ## ref https://github.com/collective/icalendar/issues/272#issuecomment-640204031
    ical_data = vobject.readOne(cal.to_ical().decode('utf-8')).serialize()
    _calendar_addics(caldav_conn, ical_data, uid, args)
    print("Added event with uid=%s" % uid)

def calendar_delete(caldav_conn, args):
    cal = find_calendar(caldav_conn, args)
    if args.event_uid:
        event = cal.event_by_uid(args.event_uid)
    elif args.event_url:
        event = cal.event_by_url(args.event_url)
    else:
        raise ValueError("Event deletion failed: either uid or url is needed")
    event.delete()

def journal_add(caldav_conn, args):
    ## TODO: copied from todo_add, should probably be consolidated
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    journal = Journal()
    ## TODO: what does the cryptic comment here really mean, and why was the dtstamp commented out?  dtstamp is required according to the RFC.
    ## TODO: (cryptic old comment:) not really correct, and it breaks i.e. with google calendar
    journal.add('dtstamp', datetime.now())
    journal.add('dtstart', date.today())
    journal.add('summary', ' '.join(args.summaryline))
    uid = uuid.uuid1()
    journal.add('uid', str(uid))
    cal.add_component(journal)
    _calendar_addics(caldav_conn, cal.to_ical(), uid, args)
    print("Added journal item with uid=%s" % uid)
    ## FULL STOP - should do some major refactoring before doing more work here!

def todo_add(caldav_conn, args):
    ## TODO: copied from calendar_add, should probably be consolidated
    if args.icalendar or args.nocaldav:
        niy(feature="add todo item by icalendar raw stdin data or create raw icalendar data to stdout")
    if args.todo_uid:
        uid = args.todo_uid
    else:
        uid = uuid.uuid1()
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    todo = Todo()
    todo.add('dtstamp', _now())

    for setarg in ('due', 'dtstart'):
        if getattr(args, 'set_'+setarg):
            if type(getattr(args, 'set_'+setarg)) == str:
                val = dateutil.parser.parse(getattr(args, 'set_'+setarg))
            else:
                val = getattr(args, 'set_'+setarg)
            todo.add(setarg, val)
    todo.add('uid', str(uid))
    todo.add('summary', ' '.join(args.summaryline))
    todo.add('status', 'NEEDS-ACTION')

    if args.is_child:
        for t in todo_select(caldav_conn, args):
            todo.add('related-to', t.instance.vtodo.uid.value)
            rt = t.instance.vtodo.add('related-to')
            rt.params['RELTYPE']=['CHILD']
            rt.value = str(uid)
            t.save()

    for attr in vtodo_txt_one:
        if attr == 'summary':
            continue
        val = getattr(args, 'set_'+attr)
        if val:
            todo.add(attr, val)
    ## TODO: this doesn't currently work quite the way we'd like it to
    ## work (it adds to lines to the ical, and vobject cares only
    ## about one of them), and if we do get it to work, we'd like to
    ## refactor and get the same logic in the edit-function
    for attr in vtodo_txt_many:
        val = getattr(args, 'set_'+attr)
        if val:
            vals = val.split(',')
            todo.add(attr, vals)

    if args.alarm is not None:
        alarm = create_alarm(' '.join(args.summaryline), parse_time_delta(args.alarm))
        todo.add_component(alarm)

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
        dtstart = _tz(args.timezone).localize(dtstart)
    else:
        dtstart = _now()
    if args.to_time:
        dtend = dateutil.parser.parse(args.to_time)
        dtend = _tz(args.timezone).localize(dtend)
    elif args.agenda_mins:
        dtend = dtstart + timedelta(minutes=args.agenda_mins)
    elif args.agenda_days:
        dtend = dtstart + timedelta(args.agenda_days)
    ## TODO - error handling if dtend is not set above - but agenda_days have a default value, so that probably won't happen

    ## TODO: time zone
    events_ = find_calendar(caldav_conn, args).date_search(dtstart, dtend, expand=True)
    events = []
    if args.icalendar:
        for ical in events_:
            print(to_normal_str(ical.data).strip())
    else:
        for event_cal in events_:
            if hasattr(event_cal.instance, 'vtimezone'):
                ## i'm not sure this is useful
                tzinfo = event_cal.instance.vtimezone.gettzinfo()
            else:
                tzinfo = _tz(args.timezone)
            events__ = event_cal.instance.components()
            for event in events__:
                if event.name != 'VEVENT':
                    continue
                dtstart = event.dtstart.value if hasattr(event, 'dtstart') else _now()
                if not isinstance(dtstart, datetime):
                    dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
                if not dtstart.tzinfo:
                    try:
                        dtstart = tzinfo.localize(dtstart)
                    except AttributeError:
                        dtstart.astimezone(tzinfo)
                ## convert into timezone given in args:
                dtstart = dtstart.astimezone(_tz(args.timezone))
                events.append({'dtstart': dtstart, 'instance': event})

        ## changed to use the "key"-parameter at 2019-09-18, as needed for python3.
        ## this will probably cause regression on sufficiently old versions of python
        events.sort(key=lambda a: a['dtstart'])
        for event in events:
            event['summary'] = "(no description)"
            event['dtstart'] = event['dtstart'].strftime(args.timestamp_format)
            for timeattr in ('dtcreated', 'dtend'):
                if hasattr(event['instance'], timeattr):
                    event[timeattr] = getattr(event['instance'], timeattr).value
                    if hasattr(event[timeattr], 'strftime'):
                        event[timeattr] = event[timeattr].strftime(args.timestamp_format)
                else:
                    event[timeattr] = '-'
            for textattr in vcal_txt_one:
                if hasattr(event['instance'], textattr):
                    event[textattr] = getattr(event['instance'], textattr).value
                else:
                    event[textattr] = '-'
            for summary_attr in ('summary', 'location', 'description'):
                if hasattr(event['instance'], summary_attr):
                    event['summary'] = getattr(event['instance'], summary_attr).value
                    break
            event['uid'] = event['instance'].uid.value if hasattr(event['instance'], 'uid') else '<no uid>'
            ## TODO: this will probably break and is probably moot on python3?
            for attr in vcal_txt_one + ['summary']:
                if isinstance(event[attr], unicode):
                    event[attr] = to_normal_str(event[attr])
            print(args.event_template.format(**event))

def create_calendar(caldav_conn, args):
    cal_obj = caldav.Principal(caldav_conn).make_calendar(cal_id=args.cal_id)
    if cal_obj:
        print("Created a calendar with id " + args.cal_id)

def create_tasklist(caldav_conn, args):
    cal_obj = caldav.Principal(caldav_conn).make_calendar(cal_id=args.cal_id, supported_calendar_component_set=['VTODO'])
    if cal_obj:
        print("Created a task list with id " + args.tasklist_id)

def todo_select(caldav_conn, args):
    if args.top+args.limit+args.offset+args.offsetn and args.todo_uid:
        raise ValueError("It doesn't make sense to combine --todo-uid with --top/--limit/--offset/--offsetn")
    if args.todo_uid:
        tasks = [ find_calendar(caldav_conn, args).todo_by_uid(args.todo_uid) ]
    else:
        ## TODO: we're fetching everything from the server, and then doing the filtering here.  It would be better to let the server do the filtering, though that requires library modifications.
        ## TODO: current release of the caldav library doesn't support the multi-key sort_keys attribute.  The try-except construct should be removed at some point in the future, when caldav 0.5 is released.
        try:
            tasks = find_calendar(caldav_conn, args).todos(sort_keys=('isnt_overdue', 'hasnt_started', 'due', 'dtstart', 'priority'))
        except:
            tasks = find_calendar(caldav_conn, args).todos()
    for attr in vtodo_txt_one + vtodo_txt_many: ## TODO: now we have _exact_ match on items in the the array attributes, and substring match on items that cannot be duplicated.  Does that make sense?  Probably not.
        if getattr(args, attr):
            tasks = [x for x in tasks if hasattr(x.instance.vtodo, attr) and getattr(args, attr) in getattr(x.instance.vtodo, attr).value]
        if getattr(args, 'no'+attr):
            tasks = [x for x in tasks if not hasattr(x.instance.vtodo, attr)]
    if args.overdue:
        tasks = [x for x in tasks if hasattr(x.instance.vtodo, 'due') and _force_datetime(x.instance.vtodo.due.value, args) < _force_datetime(datetime.now(), args)]
    if args.hide_future:
        tasks = [x for x in tasks if not(hasattr(x.instance.vtodo, 'dtstart') and _force_datetime(x.instance.vtodo.dtstart.value, args) > _force_datetime(datetime.now(), args))]
    if args.hide_parents or args.hide_children:
        tasks_by_uid = {}
        for task in tasks:
            tasks_by_uid[task.instance.vtodo.uid.value] = task
        for task in tasks:
            if hasattr(task.instance.vtodo, 'related_to'):
                uid = task.instance.vtodo.uid.value
                rel_uid = task.instance.vtodo.related_to.value
                rel_type = task.instance.vtodo.related_to.params.get('RELTYPE', 'PARENT')
                if ((rel_type == 'CHILD' and args.hide_parents) or (rel_type == 'PARENT' and args.hide_children)) and \
                   rel_uid in tasks_by_uid and uid in tasks_by_uid:
                    del tasks_by_uid[uid]
                if ((rel_type == 'PARENT' and args.hide_parents) or (rel_type == 'CHILD' and args.hide_children)) and \
                   rel_uid in tasks_by_uid:
                    del tasks_by_uid[rel_uid]
        tasks = [x for x in tasks if x.instance.vtodo.uid.value in tasks_by_uid]
    if args.top+args.limit:
        tasks = tasks[args.offset+args.offsetn:args.top+args.limit+args.offset+args.offsetn]
    elif args.offset+args.offsetn:
        tasks = tasks[args.offset+args.offsetn:]
    return tasks

def todo_edit(caldav_conn, args):
    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        ## TODO: code duplication - can we refactor this?
        for attr in vtodo_txt_one:
            if getattr(args, 'set_'+attr):
                if not hasattr(task.instance.vtodo, attr):
                    task.instance.vtodo.add(attr)
                getattr(task.instance.vtodo, attr).value = getattr(args, 'set_'+attr)
        for attr in vtodo_txt_many:
            if getattr(args, 'set_'+attr):
                if not hasattr(task.instance.vtodo, attr):
                    task.instance.vtodo.add(attr)
                getattr(task.instance.vtodo, attr).value = [ getattr(args, 'set_'+attr) ]
        for attr in vtodo_txt_many:
            if getattr(args, 'add_'+attr):
                if not hasattr(task.instance.vtodo, attr):
                    task.instance.vtodo.add(attr)
                    getattr(task.instance.vtodo, attr).value = []
                getattr(task.instance.vtodo, attr).value.append(getattr(args, 'add_'+attr))
        if args.pdb:
            import pdb; pdb.set_trace()
            ## you may now access task.data to edit the raw ical, or
            ## task.instance.vtodo to edit a vobject instance
        task.save()


def todo_postpone(caldav_conn, args):
    if args.nocaldav:
        raise ValueError("No caldav connection, aborting")
    rel_skew = None
    new_ts = None
    if args.until.startswith('+'):
        rel_skew = timedelta(seconds=int(args.until[1:-1])*time_units[args.until[-1]])
    elif args.until.startswith('in'):
        new_ts = _now()+timedelta(seconds=int(args.until[2:-1])*time_units[args.until[-1]])
    else:
        new_ts = dateutil.parser.parse(args.until)
        if not new_ts.time():
            new_ts = _date(new_ts)

    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        if new_ts:
            attr = 'due' if args.due else 'dtstart'
            if not hasattr(task.instance.vtodo, attr):
                task.instance.vtodo.add(attr)
            getattr(task.instance.vtodo, attr).value = new_ts
        if rel_skew:
            if not args.due and hasattr(task.instance.vtodo, 'dtstart'):
                task.instance.vtodo.dtstart.value += rel_skew
            elif hasattr(task.instance.vtodo, 'due'):
                task.instance.vtodo.due.value += rel_skew
            if hasattr(task.instance.vtodo, 'dtstart') and hasattr(task.instance.vtodo, 'due'):
                if type(task.instance.vtodo.dtstart.value) != type(task.instance.vtodo.due.value):
                    ## RFC states they must be of the same type
                    if isinstance(task.instance.vtodo.dtstart.value, date):
                        task.instance.vtodo.due.value = _date(task.instance.vtodo.due.value)
                    else:
                        d = task.instance.vtodo.due.value
                        task.instance.vtodo.due.value = datetime(d.year, d.month, d.day)
                    ## RFC also states that due cannot be before dtstart (and that makes sense)
                    if _force_datetime(task.instance.vtodo.dtstart.value, args) > _force_datetime(task.instance.vtodo.due.value, args):
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
            print(to_normal_str(ical.data))
    elif args.list_categories:
        categories = set()
        for task in tasks:
            if hasattr(task.instance.vtodo, 'categories'):
                categories.update(task.instance.vtodo.categories.value)
        for c in categories:
            print(c)
    else:
        for task in tasks:
            t = {'instance': task}
            t['dtstart'] = task.instance.vtodo.dtstart.value if hasattr(task.instance.vtodo,'dtstart') else date.today()
            t['dtstart_passed_mark'] = '!' if _force_datetime(t['dtstart'], args) <= _now() else ' '
            t['due'] = task.instance.vtodo.due.value if hasattr(task.instance.vtodo,'due') else date.today()+timedelta(args.default_due)
            t['due_passed_mark'] = '!' if _force_datetime(t['due'], args) < _now() else ' '
            for timeattr in ('dtstart', 'due'):
                t[timeattr] = t[timeattr].strftime(args.timestamp_format)
            for summary_attr in ('summary', 'location', 'description', 'url', 'uid'):
                if hasattr(task.instance.vtodo, summary_attr):
                    t['summary'] = getattr(task.instance.vtodo, summary_attr).value
                    break
            t['uid'] = task.instance.vtodo.uid.value
            t['summary'] = to_normal_str(t['summary'])
            print(args.todo_template.format(**t))

def todo_complete(caldav_conn, args):
    if args.nocaldav:
        raise ValueError("No caldav connection, aborting")
    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        if hasattr(task.instance.vtodo, 'rrule'):
            rrule = rrulestr(task.instance.vtodo.rrule.value)
            try:
                next = rrule.after(datetime.now())
            except TypeError: ## pesky problem with comparition of timestamps with and without tzinfo
                next = rrule.after(datetime.now(tz=tzlocal.get_localzone()))
            if next:
                ## new_task is to be completed and we keep the original task open
                completed_task = task.copy()
                remaining_task = task

                ## the remaining task should have recurrence id set to next start time, and range THISANDFUTURE
                if hasattr(remaining_task.instance.vtodo, 'recurrence_id'):
                    del remaining_task.instance.vtodo.recurrence_id
                remaining_task.instance.vtodo.add('recurrence-id')
                remaining_task.instance.vtodo.recurrence_id.value = next ## TODO: should be same type as dtstart (date or datetime)
                remaining_task.instance.vtodo.dtstart.value = next ## TODO: should be same type as dtstart (date or datetime)
                remaining_task.instance.vtodo.recurrence_id.params['RANGE'] = [ 'THISANDFUTURE' ]
                remaining_task.instance.vtodo.rrule
                remaining_task.save()

                ## the completed task should have recurrence id set to current time
                ## count in rrule should decrease
                if hasattr(completed_task.instance.vtodo, 'recurrence_id'):
                    del completed_task.instance.vtodo.recurrence_id
                completed_task.instance.vtodo.add('recurrence-id')
                completed_task.instance.vtodo.recurrence_id.value = datetime.now()
                completed_task.instance.vtodo.dtstart.value = datetime.now()
                count_search = re.search('COUNT=(\d+)', completed_task.instance.vtodo.rrule.value)
                if count_search:
                    completed_task.instance.vtodo.rrule.value = re.replace('COUNT=(\d+)', 'COUNT=%d' % int(count_search.group(1))-1)
                completed_task.complete()

                continue

        task.complete()


def todo_delete(caldav_conn, args):
    if args.nocaldav:
        raise ValueError("No caldav connection, aborting")
    tasks = todo_select(caldav_conn, args)
    for task in tasks:
        task.delete()

def config_section(config, section='default'):
    if section in config and 'inherits' in config[section]:
        ret = config_section(config, config[section]['inherits'])
    else:
        ret = {}
    if section in config:
        ret.update(config[section])
    return ret

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
        prog=__product__,
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
    conf_parser.add_argument("--version", action='version', version='%%(prog)s %s' % __version__)

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
        defaults = interactive_config(args, config, remaining_argv)
        if not remaining_argv:
            return
    else:
        defaults = config_section(config, args.config_section)
        if not 'ssl_verify_cert' in defaults:
            defaults['ssl_verify_cert'] = 'yes'
        if not 'language' in defaults:
            ## TODO: shouldn't this be lower case?
            defaults['language'] = 'EN'

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        description=__doc__,
        prog=__product__,
        # Inherit options from config_parser
        parents=[conf_parser]
        )
    parser.set_defaults(**defaults)

    ## Global options
    parser.add_argument("--nocaldav", help="Do not connect to CalDAV server, but read/write icalendar format from stdin/stdout", action="store_true")
    parser.add_argument("--icalendar", help="Read/write icalendar format from stdin/stdout", action="store_true")
    parser.add_argument("--timezone", help="Timezone to use")
    parser.add_argument('--language', help="language used")
    parser.add_argument("--caldav-url", help="Full URL to the caldav server", metavar="URL")
    parser.add_argument("--caldav-user", help="username to log into the caldav server", metavar="USER")
    parser.add_argument("--caldav-pass", help="password to log into the caldav server", metavar="PASS")
    parser.add_argument("--caldav-proxy", help="HTTP proxy server to use (if any)")
    parser.add_argument("--ssl-verify-cert", help="verification of the SSL cert - 'yes' to use the OS-provided CA-bundle, 'no' to trust any cert and the path to a CA-bundle")
    parser.add_argument("--debug-logging", help="turn on debug logging", action="store_true")
    parser.add_argument("--calendar-url", help="URL for calendar to be used (may be absolute or relative to caldav URL, or just the name of the calendar)")
    parser.add_argument("--ignoremethod", help="Ignores METHOD property if exists in the request. This violates RFC4791 but is sometimes appended by some calendar servers", action="store_true")
    parser.set_defaults(print_help=parser.print_help)

    ## TODO: check sys.argv[0] to find command
    ## TODO: set up logging
    subparsers = parser.add_subparsers(title='command')

    ## Tasks
    todo_parser = subparsers.add_parser('todo')
    todo_parser.add_argument('--top', '-1', action='count', default=0)
    todo_parser.add_argument('--offset', action='count', default=0)
    todo_parser.add_argument('--offsetn', type=int, default=0)
    todo_parser.add_argument('--limit', type=int, default=0)
    todo_parser.add_argument('--todo-uid')
    todo_parser.add_argument('--hide-parents', help='Hide the parent if you need to work on children tasks first (parent task depends on children tasks to be done first)', action='store_true')
    todo_parser.add_argument('--hide-children', help='Hide the parent if you need to work on children tasks first (parent task depends on children tasks to be done first)', action='store_true')
    todo_parser.add_argument('--overdue', help='Only show overdue tasks', action='store_true')
    todo_parser.add_argument('--hide-future', help='Hide events with future dtstart', action='store_true')

    for attr in vtodo_txt_one + vtodo_txt_many:
        todo_parser.add_argument('--'+attr, help="for filtering tasks")

    for attr in vtodo_txt_one + vtodo_txt_many:
        todo_parser.add_argument('--no'+attr, help="for filtering tasks", action='store_true')

    #todo_parser.add_argument('--priority', ....)
    #todo_parser.add_argument('--sort-by', ....)
    #todo_parser.add_argument('--due-before', ....)
    todo_parser.set_defaults(print_help=todo_parser.print_help)
    todo_subparsers = todo_parser.add_subparsers(title='tasks subcommand')
    todo_create_parser = todo_subparsers.add_parser('createlist')
    todo_create_parser.add_argument('tasklist_id')
    todo_create_parser.set_defaults(func=create_tasklist)

    todo_add_parser = todo_subparsers.add_parser('add')
    todo_add_parser.add_argument('summaryline', nargs='+')
    todo_add_parser.add_argument('--set-dtstart', default=date.today()+timedelta(1))
    todo_add_parser.add_argument('--set-due', default=date.today()+timedelta(1))
    todo_add_parser.add_argument('--is-child', help="the new task is a child-task of the selected task(s)", action='store_true')
    for attr in vtodo_txt_one + vtodo_txt_many:
        if attr != 'summary':
            todo_add_parser.add_argument('--set-'+attr, help="Set "+attr)
    # TODO: we probably want to be able to set or delete alarms in other situations, yes?  generalize?
    todo_add_parser.add_argument('--alarm', metavar='DURATION_BEFORE',
        help="specifies a time at which a reminder should be presented for this task, " \
             "relative to the start time of the task (as a timestamp delta)")
    todo_add_parser.set_defaults(func=todo_add)

    todo_list_parser = todo_subparsers.add_parser('list')
    todo_list_parser.add_argument('--todo-template', help="Template for printing out the event", default="{dtstart}{dtstart_passed_mark} {due}{due_passed_mark} {summary}")
    todo_list_parser.add_argument('--default-due', help="If a task has no due date set, list it with the due date set N days from today", type=int, default=14)
    todo_list_parser.add_argument('--list-categories', help="Instead of listing the todo-items, list the unique categories used", action='store_true')
    todo_list_parser.add_argument('--timestamp-format', help="strftime-style format string for the output timestamps", default="%Y-%m-%d (%a)")
    todo_list_parser.set_defaults(func=todo_list)

    todo_edit_parser = todo_subparsers.add_parser('edit')
    for attr in vtodo_txt_one + vtodo_txt_many:
        todo_edit_parser.add_argument('--set-'+attr, help="Set "+attr)
    for attr in vtodo_txt_many:
        todo_edit_parser.add_argument('--add-'+attr, help="Add an "+attr)
    todo_edit_parser.add_argument('--pdb', help='Allow interactive edit through the python debugger', action='store_true')
    todo_edit_parser.set_defaults(func=todo_edit)

    todo_postpone_parser = todo_subparsers.add_parser('postpone')
    todo_postpone_parser.add_argument('until', help="either a new date or +interval to add some interval to the existing time, or i.e. 'in 3d' to set the time to a new time relative to the current time.  interval is a number postfixed with a one character unit (any of smhdwy).  If the todo-item has a dtstart, this field will be modified, else the due timestamp will be modified.    If both timestamps exists and dstart will be moved beyond the due time, the due time will be set to dtime.")
    todo_postpone_parser.add_argument('--due', help="move the due, not the dtstart", action='store_true')
    todo_postpone_parser.set_defaults(func=todo_postpone)

    todo_complete_parser = todo_subparsers.add_parser('complete')
    todo_complete_parser.set_defaults(func=todo_complete)

    todo_delete_parser = todo_subparsers.add_parser('delete')
    todo_delete_parser.set_defaults(func=todo_delete)

    ## journal
    journal_parser = subparsers.add_parser('journal')
    journal_parser.set_defaults(print_help=journal_parser.print_help)
    journal_subparsers = journal_parser.add_subparsers(title='journal subcommand')
    journal_add_parser = journal_subparsers.add_parser('add')
    journal_add_parser.add_argument('summaryline', nargs='+')
    journal_add_parser.set_defaults(func=journal_add)

    calendar_parser = subparsers.add_parser('calendar')
    calendar_parser.set_defaults(print_help=calendar_parser.print_help)
    calendar_subparsers = calendar_parser.add_subparsers(title='cal subcommand')

    calendar_create_parser = calendar_subparsers.add_parser('create')
    calendar_create_parser.add_argument('cal_id')
    calendar_create_parser.set_defaults(func=create_calendar)

    calendar_add_parser = calendar_subparsers.add_parser('add')
    calendar_add_parser.add_argument('event_time', help="Timestamp and duration of the event.  See the documentation for event_time specifications")
    calendar_add_parser.add_argument('summary', nargs='+')
    calendar_add_parser.set_defaults(func=calendar_add)
    calendar_add_parser.add_argument('--whole-day', help='Whole-day event', action='store_true', default=False)
    calendar_add_parser.add_argument('--private', help='Private event', action='store_true', default=False)

    for attr in vcal_txt_one + vcal_txt_many:
        calendar_add_parser.add_argument('--set-'+attr, help='Set '+attr)

    calendar_addics_parser = calendar_subparsers.add_parser('addics')
    calendar_addics_parser.add_argument('--file', help="ICS file to upload", default='-')
    calendar_addics_parser.set_defaults(func=calendar_addics)

    calendar_agenda_parser = calendar_subparsers.add_parser('agenda')
    calendar_agenda_parser.add_argument('--from-time', help="Fetch calendar events from this timestamp.  See the documentation for time specifications.  Defaults to now")
    calendar_agenda_parser.add_argument('--to-time', help="Fetch calendar until this timestamp")
    calendar_agenda_parser.add_argument('--agenda-mins', help="Fetch calendar for so many minutes", type=int)
    calendar_agenda_parser.add_argument('--agenda-days', help="Fetch calendar for so many days", type=int, default=7)
    calendar_agenda_parser.add_argument('--event-template', help="Template for printing out the event", default="{dtstart} {summary}")
    calendar_agenda_parser.add_argument('--timestamp-format', help="strftime-style format string for the output timestamps", default="%Y-%m-%d %H:%M (%a)")
    calendar_agenda_parser.set_defaults(func=calendar_agenda)

    calendar_delete_parser = calendar_subparsers.add_parser('delete')
    calendar_delete_parser.add_argument('--event-uid')
    calendar_delete_parser.add_argument('--event-url')
    calendar_delete_parser.set_defaults(func=calendar_delete)

    args = parser.parse_args(remaining_argv)

    if args.debug_logging:
        ## TODO: set up more proper logging in a more proper way
        logging.getLogger().setLevel(logging.DEBUG)
        caldav.log.setLevel(logging.DEBUG)
        caldav.log.addHandler(logging.StreamHandler())

    if not args.nocaldav:
        if not args.calendar_url and not args.caldav_url:
            sys.stderr.write("""
missing mandatory arguments ... either calendar_url or caldav_url needs to be set
Have you set up a config file? Read the doc or ...
... use the --interactive-config option to create a config file
""")
            sys.exit(1)
        caldav_conn = caldav_connect(args)
    else:

        caldav_conn = None
    
    if args.ssl_verify_cert == 'no':
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if hasattr(args, 'func'):
        return args.func(caldav_conn, args)
    else:
        ## We get here if a subcommand is not given - in that case we should print a friendly
        ## help message.  With python2 this goes automatically, with python3 we get here.
        ## ref https://stackoverflow.com/a/22994500 subcommands are by default not required anymore
        ## in python3.  However, setting required=True gave a traceback rather than a friendly error message.
        args.print_help()

if __name__ == '__main__':
    main()
