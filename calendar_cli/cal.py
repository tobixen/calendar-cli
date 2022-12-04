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
import logging
import re
from icalendar import prop, Timezone
from calendar_cli.template import Template
from calendar_cli.config import interactive_config, config_section, read_config, expand_config_section

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
attr_time = ['dtstamp', 'dtstart', 'due', 'dtend', 'duration']
attr_int = ['priority']

def parse_dt(input, return_type=None):
    """Parse a datetime or a date.

    If return_type is date, return a date - if return_type is
    datetime, return a datetime.  If no return_type is given, try to
    guess if we should return a date or a datetime.

    """
    if isinstance(input, datetime.datetime):
        if return_type is datetime.date:
            return input.date()
        return input
    if isinstance(input, datetime.date):
        if return_type is datetime.datetime:
            return datetime.datetime.combine(input, datetime.time(0,0))
        return input
    ## dateutil.parser.parse does not recognize '+2 hours', like date does.
    if input.startswith('+'):
        return parse_add_dur(datetime.datetime.now(), input[1:])
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
    duration may be something like this:
      * 1s (one second)
      * 3m (three minutes, not months
      * 3.5h
      * 1y1w
    
    It may also be a ISO8601 duration

    Returns the dt plus duration.

    If no dt is given, return the duration.

    TODO: months not supported yet
    TODO: return of delta in years not supported yet
    TODO: ISO8601 duration not supported yet
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
            return datetime.datetime.combine(datetime.date(dt.year+i, dt.month, dt.day), dt.time())
        else:
            dur = datetime.timedelta(0, i*time_units[u])
            if dt:
                return dt + dur
            else:
                return dur
   

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

def find_calendars(args, raise_errors):
    def list_(obj):
        """
        For backward compatibility, a string rather than a list can be given as
        calendar_url, calendar_name.  Make it into a list.
        """
        if not obj:
            obj = []
        if isinstance(obj, str) or isinstance(obj, bytes):
            obj = [ obj ]
        return obj

    def _try(meth, kwargs, errmsg):
        try:
            ret = meth(**kwargs)
            assert(ret)
            return ret
        except:
            logging.error("Problems fetching calendar information: %s - skipping" % errmsg)
            if raise_errors:
                raise
            else:
                return None

    conn_params = {}
    for k in args:
        if k.startswith('caldav_') and args[k]:
            key = k[7:]
            if key == 'pass':
                key = 'password'
            if key == 'user':
                key = 'username'
            conn_params[key] = args[k]
    calendars = []
    if conn_params:
        client = caldav.DAVClient(**conn_params)
        principal = _try(client.principal, {}, conn_params['url'])
        if not principal:
            return []
        calendars = []
        tries = 0
        for calendar_url in list_(args.get('calendar_url')):
            calendar=principal.calendar(cal_id=calendar_url)
            tries += 1
            if _try(calendar.get_display_name, {}, calendar.url):
                calendars.append(calendar)
        for calendar_name in list_(args.get('calendar_name')):
            tries += 1
            calendar = _try(principal.calendar, {'name': calendar_name}, '%s : calendar "%s"' % (conn_params['url'], calendar_name))
            calendars.append(calendar)
        if not calendars and tries == 0:
            calendars = _try(principal.calendars, {}, "conn_params['url'] - all calendars")
    return calendars or []


@click.group()
## TODO: interactive config building
## TODO: language and timezone
@click.option('-c', '--config-file', default=f"{os.environ['HOME']}/.config/calendar.conf")
@click.option('--skip-config/--read-config', help="Skip reading the config file")
@click.option('--config-section', default=["default"], multiple=True)
@click.option('--caldav-url', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-username', '--caldav-user', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-password', '--caldav-pass', help="Full URL to the caldav server", metavar='URL')
@click.option('--calendar-url', help="Calendar id, path or URL", metavar='cal', multiple=True)
@click.option('--calendar-name', help="Calendar name", metavar='cal', multiple=True)
@click.option('--raise-errors/--print-errors', help="Raise errors found on calendar discovery")
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
    conns = []
    ctx.obj['calendars'] = find_calendars(kwargs, kwargs['raise_errors'])
    if not kwargs['skip_config']:
        config = read_config(kwargs['config_file'])
        if config:
            for meta_section in kwargs['config_section']:
                for section in expand_config_section(config, meta_section):
                    ctx.obj['calendars'].extend(find_calendars(config_section(config, section), raise_errors=kwargs['raise_errors']))

@cli.command()
@click.pass_context
def i_update_config(ctx):
    """
    Edit the config file interactively
    """
    raise NotImplementedError()

@cli.command()
@click.pass_context
def list_calendars(ctx):
    """
    Will output all calendars found
    """
    if not ctx.obj['calendars']:
        _abort("No calendars found!")
    else:
        output = "Accessible calendars found:\n"
        calendar_info = [(x.get_display_name(), x.url) for x in ctx.obj['calendars']]
        max_display_name = max([len(x[0]) for x in calendar_info])
        format_str= "%%-%ds %%s" % max_display_name
        click.echo_via_pager(output + "\n".join([format_str % x for x in calendar_info]) + "\n")

def _set_attr_options_(func, verb, desc=""):
    """
    decorator that will add options --set-category, --set-description etc
    """
    if verb:
        if not desc:
            desc = verb
        verb = f"{verb}-"
    else:
        verb = ""
    if verb == 'no-':
        for foo in attr_txt_one + attr_txt_many + attr_time + attr_int:
            func = click.option(f"--{verb}{foo}/--has-{foo}", default=None, help=f"{desc} ical attribute {foo}")(func)
    else:
        if verb == 'set-':
            attr__one = attr_txt_one + attr_time + attr_int
        else:
            attr__one = attr_txt_one
        for foo in attr__one:
            func = click.option(f"--{verb}{foo}", help=f"{desc} ical attribute {foo}")(func)
        for foo in attr_txt_many:
            func = click.option(f"--{verb}{foo}", help=f"{desc} ical attribute {foo}", multiple=True)(func)
    return func

def _abort(message):
    click.echo(message)
    raise click.Abort(message)

def _set_attr_options(verb="", desc=""):
    return lambda func: _set_attr_options_(func, verb, desc)

@cli.group()
@click.option('--all/--none', default=None, help='Select all (or none) of the objects.  Overrides all other selection options.')
@click.option('--uid', multiple=True, help='select an object with a given uid (or select more object with given uids).  Overrides all other selection options')
@click.option('--abort-on-missing-uid/--ignore-missing-uid', default=False, help='Abort if (one or more) uids are not found (default: silently ignore missing uids).  Only effective when used with --uid')
@click.option('--todo/--no-todo', default=None, help='select only todos (or no todos)')
@click.option('--event/--no-event', default=None, help='select only events (or no events)')
@click.option('--include-completed/--exclude-completed', default=False, help='select only todos (or no todos)')
@_set_attr_options(desc="select by")
@_set_attr_options('no', desc="select objects without")
@click.option('--start', help='do a time search, with this start timestamp')
@click.option('--end', help='do a time search, with this end timestamp (or duration)')
@click.option('--timespan', help='do a time search for this interval')
@click.option('--sort-key', help='use this attributes for sorting.  Templating can be used.  Prepend with - for reverse sort.  Special: "get_duration()" yields the duration or the distance between dtend and dtstart, or an empty timedelta', multiple=True)
@click.option('--skip-parents/--include-parents', help="Skip parents if it's children is selected.  Useful for finding tasks that can be started if parent depends on child", default=False)
@click.option('--skip-children/--include-children', help="Skip children if it's parent is selected.  Useful for getting an overview of the big picture if children are subtasks", default=False)
@click.option('--limit', help='Number of objects to show', type=int)
@click.option('--offset', help='SKip the first objects', type=int)
@click.pass_context
def select(*largs, **kwargs):
    """Search command, allows listing, editing, etc

    This command is intended to be used every time one is to
    select/filter/search for one or more events/tasks/journals.  It
    offers a simple templating language built on top of python
    string.format for sorting and listing.  It offers several
    subcommands for doing things on the objects found.

    The command is powerful and complex, but may also be non-trivial
    in usage - hence there are some convenience-commands built for
    allowing the common use-cases to be done in easier ways (like
    agenda and fix-tasks-interactive)
    """
    return _select(*largs, **kwargs)

def _select(ctx, all=None, uid=[], abort_on_missing_uid=None, sort_key=[], skip_parents=None, skip_children=None, limit=None, offset=None, **kwargs_):
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

    if kwargs_.get('start'):
        kwargs['start'] = parse_dt(kwargs['start'])
        if kwargs_.get('end'):
            rx = re.match(r'\+((\d+(\.\d+)?[smhdwy])+)', kwargs['end'])
            if rx:
                kwargs['end'] = parse_add_dur(kwargs['start'], rx.group(1))
            else:
                kwargs['end'] = parse_dt(kwargs['end'])
    elif kwargs_.get('timespan'):
        kwargs['start'], kwargs['end'] = parse_timespec(kwargs['timespan'])

    for attr in attr_txt_many:
        if len(kwargs_.get(attr, []))>1:
            raise NotImplementedError(f"is it really needed to search for more than one {attr}?")
        elif kwargs_.get(attr):
            kwargs[attr] = kwargs[attr][0]

    ## TODO: special handling of parent and child! (and test for that!)

    if 'start' in kwargs and 'end' in kwargs:
        kwargs['expand'] = True
    for c in ctx.obj['calendars']:
        objs.extend(c.search(**kwargs))

    if skip_children or skip_parents:
        objs_by_uid = {}
        for obj in objs:
            objs_by_uid[obj.icalendar_component['uid']] = obj
        for obj in objs:
            rels = obj.icalendar_component.get('RELATED-TO', [])
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
            fkey = lambda obj: Template(skey).format(**obj.icalendar_component)
        elif skey == 'get_duration()':
            fkey = lambda obj: obj.get_duration()
        elif skey in ('DTSTART', 'DTEND', 'DUE', 'DTSTAMP'):
            fkey = lambda obj: getattr(obj.icalendar_component.get(skey), 'dt', datetime.datetime(1970,1,2)).strftime("%F%H%M%S")
        else:
            fkey = lambda obj: obj.icalendar_component.get(skey)
        ctx.obj['objs'].sort(key=fkey, reverse=reverse)

    ## OPTIMIZE TODO: this is also suboptimal, if ctx.obj is a very long list
    if offset is not None:
        ctx.obj['objs'] = ctx.obj['objs'][offset:]
    if limit is not None:
        ctx.obj['objs'] = ctx.obj['objs'][0:limit]

    ## some sanity checks
    for obj in ctx.obj['objs']:
        comp = obj.icalendar_component
        dtstart = comp.get('dtstart')
        dtend = comp.get('dtend') or comp.get('due')
        if dtstart and dtend and dtstart.dt > dtend.dt:
            logging.error(f"task with uuid {comp['uid']} as dtstart after dtend/due")

@select.command()
@click.pass_context
def list_categories(ctx):
    """
    List all categories used in the selection
    """
    cats = _cats(ctx)
    for c in cats:
        click.echo(c)

def _cats(ctx):
    categories = set()
    for obj in ctx.obj['objs']:
        cats = obj.icalendar_component.get('categories')
        if cats:
            categories.update(cats.cats)
    return categories

list_type = list

@select.command()
@click.option('--ics/--no-ics', default=False, help="Output in ics format")
@click.option('--template', default="{DTSTART.dt:?{DUE.dt:?(date missing)?}?%F %H:%M:%S}: {SUMMARY:?{DESCRIPTION:?(no summary given)?}?}")
@click.pass_context
def list(ctx, ics, template):
    """
    Print out a list of tasks/events/journals
    """
    return _list(ctx, ics, template)

def _list(ctx, ics=False, template="{DTSTART.dt:?{DUE.dt:?(date missing)?}?%F %H:%M:%S}: {SUMMARY:?{DESCRIPTION:?(no summary given)?}?}"):
    """
    Actual implementation of list
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
    output = []
    for obj in ctx.obj['objs']:
        if isinstance(obj, str):
            output.append(obj)
            continue
        for sub in obj.icalendar_instance.subcomponents:
            if not isinstance(sub, Timezone):
                output.append(template.format(**sub))
    click.echo_via_pager("\n".join(output))

@select.command()
@click.pass_context
def print_uid(ctx):
    """
    Convenience command, prints UID of first item

    This can also be achieved by using select with template and limit
    """
    click.echo(ctx.obj['objs'][0].icalendar_component['UID'])

@select.command()
@click.option('--multi-delete/--no-multi-delete', default=None, help="Delete multiple things without confirmation prompt")
@click.pass_context
def delete(ctx, multi_delete, **kwargs):
    """
    Delete the selected item(s)
    """
    objs = ctx.obj['objs']
    if multi_delete is None and len(objs)>1:
        multi_delete = click.confirm(f"OK to delete {len(objs)} items?")
    if len(objs)>1 and not multi_delete:
        _abort(f"Not going to delete {len(objs)} items")
    for obj in objs:
        obj.delete()

@select.command()
@click.option('--pdb/--no-pdb', default=None, help="Interactive edit through pdb (experts only)")
@click.option('--add-category', default=None, help="Delete multiple things without confirmation prompt", multiple=True)
@click.option('--complete/--uncomplete', default=None, help="Mark task(s) as completed")
@click.option('--complete-recurrence-mode', default='safe', help="Completion of recurrent tasks, mode to use - can be 'safe', 'thisandfuture' or '' (see caldav library for details)")
@_set_attr_options(verb='set')
@click.pass_context
def edit(*largs, **kwargs):
    """
    Edits a task/event/journal
    """
    return _edit(*largs, **kwargs)

def _edit(ctx, add_category=None, complete=None, complete_recurrence_mode='safe', **kwargs):
    """
    Edits a task/event/journal
    """
    if 'recurrence_mode' in kwargs:
        complete_recurrence_mode = kwargs.pop('recurrence_mode')
    _process_set_args(ctx, kwargs)
    for obj in ctx.obj['objs']:
        component = obj.icalendar_component
        if kwargs.get('pdb'):
            click.echo("icalendar component available as component")
            click.echo("caldav object available as obj")
            click.echo("do the necessary changes and press c to continue normal code execution")
            click.echo("happy hacking")
            import pdb; pdb.set_trace()
        for arg in ctx.obj['set_args']:
            if arg in ('child', 'parent'):
                obj.set_relation(arg, ctx.obj['set_args'][arg])
            elif arg == 'duration':
                duration = parse_add_dur(dt=None, dur=ctx.obj['set_args'][arg])
                obj.set_duration(duration)
            else:
                if arg in component:
                    component.pop(arg)
                component.add(arg, ctx.obj['set_args'][arg])
        if add_category:
            if 'categories' in component:
                cats = component.pop('categories').cats
            else:
                cats = []
            cats.extend(add_category)
            component.add('categories', cats)
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
    Convenience command, mark tasks as completed

    The same result can be obtained by running this subcommand:

      `edit --complete`
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

@cli.command()
@click.pass_context
def i_set_task_attribs(ctx):
    """Interactively populate missing attributes to tasks

    Convenience method for tobixen-style task management.  Assumes
    that all tasks ought to have categories, a due date, a priority
    and a duration (estimated minimum time to do the task) set and ask
    for those if it's missing.

    See also USER_GUIDE.md, TASK_MANAGEMENT.md and NEXT_LEVEL.md
    """
    ## Tasks missing a category
    LIMIT = 16

    def _set_something(something, help_text, default=None):
        cond = {f"no_{something}": True}
        if something == 'duration':
            cond['no_dtstart'] = True
        _select(ctx=ctx, todo=True, limit=LIMIT, sort_key=['{DTSTART.dt:?{DUE.dt:?(0000)?}?%F %H:%M:%S}', '{PRIORITY:?0?}'], **cond)
        objs = ctx.obj['objs']
        if objs:
            num = len(objs)
            if num == LIMIT:
                num = f"{LIMIT} or more"
            click.echo(f"There are {num} tasks with no {something} set.")
            if something == 'category':
                _select(ctx=ctx, todo=True)
                cats = list_type(_cats(ctx))
                cats.sort()
                click.echo("List of existing categories in use (if any):")
                click.echo("\n".join(cats))
            click.echo(f"For each task, {help_text}")
            for obj in objs:
                comp = obj.icalendar_component
                summary = comp.get('summary') or comp.get('description') or comp.get('uid')
                value = click.prompt(summary)
                if not value and default:
                    value = default
                if something == 'category':
                    comp.add('categories', value.split(','))
                elif something == 'due':
                    obj.set_due(parse_dt(value), move_dtstart=True)
                elif something == 'duration':
                    obj.set_duration(parse_add_dur(None, value), movable_attr='DTSTART')
                else:
                    comp.add(something, value)
                obj.save()
            click.echo()

    ## Tasks missing categories
    _set_something('category', "enter a comma-separated list of categories to be added")

    ## Tasks missing a due date
    _set_something('due', "enter the due date (default +2d)", default="+2d")

    ## Tasks missing a priority date
    message="""Enter the priority - a number between 0 and 9.

The RFC says that 0 is undefined, 1 is highest and 9 is lowest.

TASK_MANAGEMENT.md suggests the following:

1: The DUE timestamp MUST be met, come hell or high water.
2: The DUE timestamp SHOULD be met, if we lose it the task becomes irrelevant.
3: The DUE timestamp SHOULD be met, but worst case we can probably procrastinate it, perhaps we can apply for an extended deadline.
4: The deadline SHOULD NOT be pushed too much
5: If the deadline approaches and we have higher-priority tasks that needs to be done, then this task can be procrastinated.
6: The DUE is advisory only and expected to be pushed - but it would be nice if the task gets done within reasonable time.
7-9: Low-priority task, it would be nice if the task gets done at all ... but the DUE is overly optimistic and expected to be pushed several times.
"""
    
    _set_something('priority', message, default="5")

    ## Tasks missing a duration
    message="""Enter the DURATION (i.e. 5h or 2d)

TASK_MANAGEMENT.md suggests this to be the estimated efficient work time
needed to complete the task.

(According to the RFC, DURATION cannot be combined with DUE, meaning that we
actually will be setting DTSTART and not DURATION)"""

    _set_something('duration', message)

@cli.command()
@click.pass_context
def agenda(ctx):
    """
    Convenience command, prints an agenda

    This command is slightly redundant, same results may be obtained by running those two commands in series:
    
      `select --event --start=now --end=in 32 days --limit=16 list`
    
      `select --todo --sort '{DTSTART.dt:?{DUE.dt:?(0000)?}?%F %H:%M:%S}' --sort '{PRIORITY:?0}' --limit=16 list`

    agenda is for convenience only and takes no options or parameters.
    Use the select command for advanced usage.  See also USAGE.md.
    """
    start = datetime.datetime.now()
    _select(ctx=ctx, start=start, event=True, end='+30d', limit=16, sort_key=['DTSTART', 'get_duration()'])
    objs = ctx.obj['objs']
    _select(ctx=ctx, start=start, todo=True, end='+30d', limit=16, sort_key=['{DTSTART.dt:?{DUE.dt:?(0000)?}?%F %H:%M:%S}', '{PRIORITY:?0?}'])
    ctx.obj['objs'] = objs + ["======"] + ctx.obj['objs']
    return _list(ctx)

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
    for arg in ctx.obj['set_args']:
        if arg in attr_time and arg != 'duration':
            ctx.obj['set_args'][arg] = parse_dt(ctx.obj['set_args'][arg])

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
