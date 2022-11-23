#!/usr/bin/env python

"""https://github.com/tobixen/calendar-cli/ - high-level cli against caldav servers.

Copyright (C) 2013-2022 Tobias Brox and other contributors.

See https://www.gnu.org/licenses/gpl-3.0.en.html for license information.

This is a new cli to be fully released in version 1.0, until then
quite much functionality will only be available through the legacy
calendar-cli.  For discussions on the directions, see
https://github.com/tobixen/calendar-cli/issues/88
"""

## This file should preferably just be a thin interface between public
## python libraries and the command line.  Logics that isn't strictly
## tied to the cli as such but also does not fit into other libraries
## may be moved out to a separate library file.

## This file aims to be smaller than the old calendar-cli while
## offering more featuores.

from calendar_cli.metadata import metadata
__version__ = metadata["version"]

import click
import os
import caldav
#import isodate
import dateutil
import dateutil.parser
import datetime
import re
from icalendar import prop
from calendar_cli.template import Template

list_type = list

## should make some subclasses of click.ParamType:

## class DateOrDateTime - perhaps a subclass of click.DateTime, returns date
## if no time is given (can probably just be subclassed directly from
## click.DateTime?

## class DurationOrDateTime - perhaps a subclass of the above, should attempt
## to use pytimeparse if the given info is not a datetime.

## See https://click.palletsprojects.com/en/8.0.x/api/#click.ParamType and
## /usr/lib/*/site-packages/click/types.py on how to do this.

## TODO: maybe find those attributes through the icalendar library? icalendar.cal.singletons, icalendar.cal.multiple, etc
attr_txt_one = ['location', 'description', 'geo', 'organizer', 'summary', 'class', 'rrule']
attr_txt_many = ['category', 'comment', 'contact', 'resources', 'parent', 'child']

def parse_dt(input, return_type=None):
    """Parse a datetime or a date.

    If return_type is date, return a date - if return_type is
    datetime, return a datetime.  If no return_type is given, try to
    guess if we should return a date or a datetime.

    """
    ret = dateutil.parser.parse(input)
    if return_type is datetime.datetime:
        return ret
    elif return_type is datetime.date:
        return ret.date()
    elif ret.time() == datetime.time(0,0) and len(input)<12 and not '00:00' in input and not '0000' in input:
        return ret.date()
    else:
        return ret

def parse_add_dur(dt, dur):
    """
    duration may be something on the format 1s (one second), 3m (three minutes, not months), 3.5h, 1y1w, etc
    or a ISO8601 duration (TODO: not supported yet).  Return the dt plus duration
    """
    time_units = {
        's': 1, 'm': 60, 'h': 3600,
        'd': 86400, 'w': 604800
    }
    while dur:
        rx = re.match(r'(\d+(?:\.\d+)?)([smhdw])(.*)', dur)
        assert rx
        i = float(rx.group(1))
        u = rx.group(2)
        dur = rx.group(3)
        if u=='y':
            dt = datetime.datetime.combine(datetime.date(dt.year+i, dt.month, dt.day), dt.time())
        else:
            dt = dt + datetime.timedelta(0, i*time_units[u])
    return dt
   

## TODO ... (and should be moved somewhere else?)
def parse_timespec(timespec):
    """parses a timespec and return two timestamps

    The ISO8601 interval format, format 1, 2 or 3 as described at
    https://en.wikipedia.org/wiki/ISO_8601#Time_intervals should be
    accepted, though it may be dependent on
    https://github.com/gweis/isodate/issues/77 or perhaps
    https://github.com/dateutil/dateutil/issues/1184 
    
    The calendar-cli format (i.e. 2021-01-08 15:00:00+1h) should be accepted

    Two timestamps should be accepted.

    One timestamp should be accepted, and the second return value will be None.
    """
    ## calendar-cli format, 1998-10-03 15:00+2h
    if '+' in timespec:
        rx = re.match(r'(.*)\+((?:\d+(?:\.\d+)?[smhdwy])+)$', timespec)
        if rx:
            start = parse_dt(rx.group(1))
            end = parse_add_dur(start, rx.group(2))
            return (start, end)
    try:
        ## parse("2015-05-05 2015-05-05") does not throw the ParserError
        if timespec.count('-')>3:
            raise dateutil.parser.ParserError("Seems to be two dates here")
        ret = parse_dt(timespec)
        return (ret,None)
    except dateutil.parser.ParserError:
        split_by_space = timespec.split(' ')
        if len(split_by_space) == 2:
            return (parse_dt(split_by_space[0]), parse_dt(split_by_space[1]))
        elif len(split_by_space) == 4:
            return (parse_dt(f"{split_by_space[0]} {split_by_space[1]}"), parse_dt(f"{split_by_space[2]} {split_by_space[3]}"))
        else:
            raise ValueError(f"couldn't parse time interval {timespec}")

    raise NotImplementedError("possibly a ISO time interval")

@click.group()
## TODO
#@click.option('-c', '--config-file', type=click.File("rb"), default=f"{os.environ['HOME']}/.config/calendar.conf")
#@click.option('--config-section', default="default")
@click.option('--caldav-url', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-username', '--caldav-user', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-password', '--caldav-pass', help="Full URL to the caldav server", metavar='URL')
@click.option('--calendar-url', help="Calendar id, path or URL", metavar='cal', multiple=True)
@click.option('--calendar-name', help="Calendar name", metavar='cal', multiple=True)
@click.pass_context
def cli(ctx, **kwargs):
    """
    CalDAV Command Line Interface, in development.

    This command will eventually replace calendar-cli.
    It's not ready for consumption.  Only use if you want to contribute/test.
    """
    ## The cli function will prepare a context object, a dict containing the
    ## caldav_client, principal and calendar
    
    ctx.ensure_object(dict)
    ## TODO: add all relevant connection parameters for the DAVClient as options
    ## TODO: logic to read the config file and edit kwargs from config file
    ## TODO: delayed communication with caldav server (i.e. if --help is given to subcommand)
    ## TODO: catch errors, present nice error messages
    conn_params = {}
    for k in kwargs:
        if k.startswith('caldav_'):
            conn_params[k[7:]] = kwargs[k]
    client = caldav.DAVClient(**conn_params)
    principal = client.principal()
    calendars = []
    for calendar_url in kwargs['calendar_url']:
        calendars.append(principal.calendar(cal_id=calendar_url))
    for calendar_name in kwargs['calendar_name']:
        calendars.append(principal.calendar(name=calendar_name))
    if not calendars:
        calendars = principal.calendars()
    ctx.obj['calendars'] = calendars

@cli.command()
@click.pass_context
def test(ctx):
    """
    Will test that we can connect to the caldav server and find the calendars.
    """
    click.echo("Seems like everything is OK")

def _set_attr_options_(func, verb):
    """
    decorator that will add options --set-category, --set-description etc
    """
    if verb:
        verb1 = f"{verb}-"
    else:
        verb1 = ""
        verb = "Select by "
    for foo in attr_txt_one:
        func = click.option(f"--{verb1}{foo}", help=f"{verb} ical attribute {foo}")(func)
    for foo in attr_txt_many:
        func = click.option(f"--{verb1}{foo}", help=f"{verb} ical attribute {foo}", multiple=True)(func)
    return func

def _abort(message):
    click.echo(message)
    raise click.Abort(message)

def _set_attr_options(verb=""):
    return lambda func: _set_attr_options_(func,verb)

@cli.group()
@click.option('--all/--none', default=None, help='Select all (or none) of the objects.  Overrides all other selection options.')
@click.option('--uid', multiple=True, help='select an object with a given uid (or select more object with given uids).  Overrides all other selection options')
@click.option('--abort-on-missing-uid/--ignore-missing-uid', default=False, help='Abort if (one or more) uids are not found (default: silently ignore missing uids).  Only effective when used with --uid')
@click.option('--todo/--notodo', default=None, help='select only todos (or no todos)')
@click.option('--event/--noevent', default=None, help='select only todos (or no todos)')
@click.option('--include-completed/--exclude-completed', default=False, help='select only todos (or no todos)')
@_set_attr_options()
@click.option('--start', help='do a time search, with this start timestamp')
@click.option('--end', help='do a time search, with this end timestamp (or duration)')
@click.option('--timespan', help='do a time search for this interval')
@click.option('--sort-key', help='use this attributes for sorting.  Templating can be used.  Prepend with - for reverse sort', multiple=True)
@click.option('--skip-parents/--include-parents', help="Skip parents if it's children is selected.  Useful for finding tasks that can be started if parent depends on child", default=False)
@click.option('--skip-children/--include-children', help="Skip children if it's parent is selected.  Useful for getting an overview of the big picture if children are subtasks", default=False)
@click.option('--limit', help='Number of objects to show', type=int)
@click.option('--offset', help='SKip the first objects', type=int)
@click.pass_context
def select(ctx, all, uid, abort_on_missing_uid, sort_key, skip_parents, skip_children, limit, offset, **kwargs_):
    """
    select/search/filter tasks/events, for listing/editing/deleting, etc
    """
    objs = []
    ctx.obj['objs'] = objs

    ## TODO: move all search/filter/select logic to caldav library?
    
    ## handle all/none options
    if all is False: ## means --none.
        return
    if all:
        for c in ctx.obj['calendars']:
            objs.extend(c.objects())
        return

    kwargs = {}
    for kw in kwargs_:
        if kwargs_[kw] is not None and kwargs_[kw] != ():
            kwargs[kw] = kwargs_[kw]

    ## uid(s)
    missing_uids = []
    for uid_ in uid:
        comp_filter=None
        if kwargs_['event']:
            comp_filter='VEVENT'
        if kwargs_['todo']:
            comp_filter='VTODO'
        cnt = 0
        for c in ctx.obj['calendars']:
            try:
                objs.append(c.object_by_uid(uid_, comp_filter=comp_filter))
                cnt += 1
            except caldav.error.NotFoundError:
                pass
        if not cnt:
            missing_uids.append(uid_)
    if abort_on_missing_uid and missing_uids:
        _abort(f"Did not find the following uids in any calendars: {missing_uids}")
    if uid:
        return

    if kwargs_['start']:
        kwargs['start'] = parse_dt(kwargs['start'])
        if kwargs_['end']:
            rx = re.match(r'\+((\d+(\.\d+)?[smhdwy])+)', kwargs['end'])
            if rx:
                kwargs['end'] = parse_add_dur(kwargs['start'], rx.group(1))
            else:
                kwargs['end'] = parse_dt(kwargs['end'])
    elif kwargs_['timespan']:
        kwargs['start'], kwargs['end'] = parse_timespec(kwargs['timespan'])

    for attr in attr_txt_many:
        if len(kwargs_[attr])>1:
            raise NotImplementedError(f"is it really needed to search for more than one {attr}?")
        elif kwargs_[attr]:
            kwargs[attr] = kwargs[attr][0]

    ## TODO: special handling of parent and child! (and test for that!)

    for c in ctx.obj['calendars']:
        objs.extend(c.search(**kwargs))

    if skip_children or skip_parents:
        objs_by_uid = {}
        for obj in objs:
            objs_by_uid[obj.icalendar_instance.subcomponents[0]['uid']] = obj
        for obj in objs:
            rels = obj.icalendar_instance.subcomponents[0].get('RELATED-TO', [])
            rels = rels if isinstance(rels, list_type) else [ rels ]
            for rel in rels:
                rel_uid = rel
                rel_type = rel.params.get('REL-TYPE', None)
                if ((rel_type == 'CHILD' and skip_parents) or (rel_type == 'PARENT' and skip_children)) and rel_uid in objs_by_uid and uid in objs_by_uid:
                    del objs_by_uid[uid]
                if ((rel_type == 'PARENT' and skip_parents) or (rel_type == 'CHILD' and skip_children)) and rel_uid in objs_by_uid:
                    del objs_by_uid[rel_uid]
        objs = objs_by_uid.values()

    ## OPTIMIZE TODO: sorting the list multiple times rather than once is a bit of brute force, if there are several sort keys and long list of objects, we should sort once and consider all sort keys while sorting
    ## TODO: Consider that an object may be expanded and contain lots of event instances.  We will then need to expand the caldav.Event object into multiple objects, each containing one recurrance instance.  This should probably be done on the caldav side of things.
    for skey in reversed(sort_key):
        ## If the key starts with -, sorting should be reversed
        if skey[0] == '-':
            reverse = True
            skey=skey[1:]
        else:
            reverse = False
        ## if the key contains {}, it should be considered to be a template
        if '{' in skey:
            fkey = lambda obj: Template(skey).format(**obj.icalendar_instance.subcomponents[0])
        else:
            fkey = lambda obj: obj.icalendar_instance.subcomponents[0][skey]
        ctx.obj['objs'].sort(key=fkey, reverse=reverse)

    ## OPTIMIZE TODO: this is also suboptimal, if ctx.obj is a very long list
    if offset is not None:
        ctx.obj['objs'] = ctx.obj['objs'][offset:]
    if limit is not None:
        ctx.obj['objs'] = ctx.obj['objs'][0:limit]

@select.command()
@click.option('--ics/--no-ics', default=False, help="Output in ics format")
@click.option('--template', default="{DUE.dt:?{DTSTART.dt:?(date missing)?}?:%F %H:%M:%S}: {SUMMARY:?{DESCRIPTION:?(no summary given)?}?}")
@click.pass_context
def list(ctx, ics, template):
    """
    print out a list of tasks/events/journals
    """
    if ics:
        if not ctx.obj['objs']:
            return
        icalendar = ctx.obj['objs'].pop(0).icalendar_instance
        for obj in ctx.obj['objs']:
            icalendar.subcomponents.extend(obj.icalendar_instance.subcomponents)
        click.echo(icalendar.to_ical())
        return
    template=Template(template)
    for obj in ctx.obj['objs']:
        for sub in obj.icalendar_instance.subcomponents:
            click.echo(template.format(**sub))

@select.command()
@click.pass_context
def print_uid(ctx):
    click.echo(ctx.obj['objs'][0].icalendar_instance.subcomponents[0]['UID'])

@select.command()
@click.option('--multi-delete/--no-multi-delete', default=None, help="Delete multiple things without confirmation prompt")
@click.pass_context
def delete(ctx, multi_delete, **kwargs):
    """
    delete the selected item(s)
    """
    objs = ctx.obj['objs']
    if multi_delete is None and len(objs)>1:
        multi_delete = click.confirm(f"OK to delete {len(objs)} items?")
    if len(objs)>1 and not multi_delete:
        _abort(f"Not going to delete {len(objs)} items")
    for obj in objs:
        obj.delete()

@select.command()
@click.option('--add-category', default=None, help="Delete multiple things without confirmation prompt", multiple=True)
@click.option('--complete/--uncomplete', default=None, help="Mark task(s) as completed")
@click.option('--complete-recurrence-mode', default='safe', help="Completion of recurrent tasks, mode to use - can be 'safe', 'thisandfuture' or '' (see caldav library for details)")
@_set_attr_options(verb='set')
@click.pass_context
def edit(*largs, **kwargs):
    return _edit(*largs, **kwargs)

def _edit(ctx, add_category=None, complete=None, complete_recurrence_mode='safe', **kwargs):
    """
    Edits a task/event/journal
    """
    if 'recurrence_mode' in kwargs:
        complete_recurrence_mode = kwargs.pop('recurrence_mode')
    _process_set_args(ctx, kwargs)
    for obj in ctx.obj['objs']:
        ie = obj.icalendar_instance.subcomponents[0]
        for arg in ctx.obj['set_args']:
            if arg in ('child', 'parent'):
                obj.set_relation(arg, ctx.obj['set_args'][arg])
            else:
                if arg in ie:
                    ie.pop(arg)
                ie.add(arg, ctx.obj['set_args'][arg])
        if add_category:
            if 'categories' in ie:
                cats = ie.pop('categories').cats
            else:
                cats = []
            cats.extend(add_category)
            ie.add('categories', cats)
        if complete:
            obj.complete(handle_rrule=complete_recurrence_mode, rrule_mode=complete_recurrence_mode)
        elif complete is False:
            obj.uncomplete()
        obj.save()


@select.command()
@click.pass_context
@click.option('--recurrence-mode', default='safe', help="Completion of recurrent tasks, mode to use - can be 'safe', 'thisandfuture' or '' (see caldav library for details)")
def complete(ctx, **kwargs):
    """
    Mark tasks as completed (alias for edit --complete)
    """
    return _edit(ctx, complete=True, **kwargs)

@select.command()
@click.pass_context
def calculate_panic_time(ctx, **kwargs):
    raise NotImplementedError()

@select.command()
@click.pass_context
def sum_hours(ctx, **kwargs):
    raise NotImplementedError()

## TODO: all combinations of --first-calendar, --no-first-calendar, --multi-add, --no-multi-add should be tested
@cli.group()
@click.option('-l', '--add-ical-line', multiple=True, help="extra ical data to be injected")
@click.option('--multi-add/--no-multi-add', default=None, help="Add things to multiple calendars")
@click.option('--first-calendar/--no-first-calendar', default=None, help="Add things only to the first calendar found")
@click.pass_context
def add(ctx, **kwargs):
    """
    Save new objects on calendar(s)
    """
    if len(ctx.obj['calendars'])>1 and kwargs['multi_add'] is False:
        _abort("Giving up: Multiple calendars given, but --no-multi-add is given")
    ## TODO: crazy-long if-conditions can be refactored - see delete on how it's done there
    if (kwargs['first_calendar'] or
        (len(ctx.obj['calendars'])>1 and
         not kwargs['multi_add'] and
         not click.confirm(f"Multiple calendars given.  Do you want to duplicate to {len(ctx.obj['calendars'])} calendars? (tip: use option --multi-add to avoid this prompt in the future)"))):
        calendar = ctx.obj['calendars'][0]
        ## TODO: we need to make sure f"{calendar.name}" will always work or something
        if (kwargs['first_calendar'] is not None and
            (kwargs['first_calendar'] or
            click.confirm(f"First calendar on the list has url {calendar.url} - should we add there? (tip: use --calendar-url={calendar.url} or --first_calendar to avoid this prompt in the future)"))):
            ctx.obj['calendars'] = [ calendar ]
        else:
            _abort("Giving up: Multiple calendars found/given, please specify which calendar you want to use")

    ctx.obj['ical_fragment'] = "\n".join(kwargs['add_ical_line'])

@add.command()
@click.pass_context
@click.option('-d', '--ical-data', '--ical', help="ical object to be added")
@click.option('-f', '--ical-file', type=click.File('rb'), help="file containing ical data")
def ical(ctx, ical_data, ical_file):
    if (ical_file):
        ical = ical_file.read()
    if ctx.obj['ical_fragment']:
        ical = ical.replace('\nEND:', f"{ctx.obj['ical_fragment']}\nEND:")
    for c in ctx.obj['calendars']:
        ## TODO: this may not be an event - should make a Calendar.save_object method
        c.save_event(ical)

def _process_set_args(ctx, kwargs):
    ctx.obj['set_args'] = {}
    for x in kwargs:
        if kwargs[x] is None or kwargs[x]==():
            continue
        if x == 'set_rrule':
            rrule = {}
            for split1 in kwargs[x].split(';'):
                k,v = split1.split('=')
                rrule[k] = v
            ctx.obj['set_args']['rrule'] = rrule
        elif x == 'set_category':
            ctx.obj['set_args']['categories'] = kwargs[x]
        elif x.startswith('set_'):
            ctx.obj['set_args'][x[4:]] = kwargs[x]
    if 'summary' in kwargs:
        ctx.obj['set_args']['summary'] = ctx.obj['set_args'].get('summary', '') + kwargs['summary']
    if 'ical_fragment' in kwargs:
        ctx.obj['set_args']['ics'] = kwargs['ical_fragment']

@add.command()
@click.argument('summary', nargs=-1)
@_set_attr_options(verb='set')
@click.pass_context
def todo(ctx, **kwargs):
    """
    Creates a new task with given SUMMARY

    Examples: 

    kal add todo "fix all known bugs in calendar-cli"
    kal add todo --set-due=2050-12-10 "release calendar-cli version 42.0.0"
    """
    kwargs['summary'] = " ".join(kwargs['summary'])
    _process_set_args(ctx, kwargs)
    if not ctx.obj['set_args']['summary']:
        _abort("denying to add a TODO with no summary given")
        return
    for cal in ctx.obj['calendars']:
        todo = cal.save_todo(ical=ctx.obj['ical_fragment'], **ctx.obj['set_args'], no_overwrite=True)
        click.echo(f"uid={todo.id}")

@add.command()
## TODO
@click.argument('summary')
@click.argument('timespec')
@_set_attr_options(verb='set')
@click.pass_context
def event(ctx, timespec, **kwargs):
    """
    Creates a new event with given SUMMARY at the time specifed through TIMESPEC.

    TIMESPEC is an ISO-formatted date or timestamp, optionally with a postfixed interval
.
    Examples:

    kal add event "final bughunting session" 2004-11-25+5d
    kal add event "release party" 2004-11-30T19:00+2h
    """
    _process_set_args(ctx, kwargs)
    for cal in ctx.obj['calendars']:
        (dtstart, dtend) = parse_timespec(timespec)
        event = cal.save_event(dtstart=dtstart, dtend=dtend, **ctx.obj['set_args'], no_overwrite=True)
        click.echo(f"uid={event.id}")

def journal():
    click.echo("soon you should be able to add journal entries to your calendar")
    raise NotImplementedError("foo")

if __name__ == '__main__':
    cli()
