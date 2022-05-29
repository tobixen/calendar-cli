#!/usr/bin/env python

"""https://github.com/tobixen/calendar-cli/ - high-level cli against caldav servers.

Copyright (C) 2013-2021 Tobias Brox and other contributors.

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

from calendar_cli import __version__

import click
import os
import caldav

## should make some subclasses of click.ParamType:

## class DateOrDateTime - perhaps a subclass of click.DateTime, returns date
## if no time is given (can probably just be subclassed directly from
## click.DateTime?

## class DurationOrDateTime - perhaps a subclass of the above, should attempt
## to use pytimeparse if the given info is not a datetime.

## See https://click.palletsprojects.com/en/8.0.x/api/#click.ParamType and
## /usr/lib/*/site-packages/click/types.py on how to do this.

## TODO: maybe find those attributes through the icalendar library?
attr_txt_one = ['location', 'description', 'geo', 'organizer', 'summary']
attr_txt_many = ['categories', 'comment', 'contact', 'resources']

## TODO ... (and should be moved somewhere else)
def _parse_timespec(timespec):
    """
    will parse a timespec and return two timestamps.  timespec can be
    in ISO8601 interval format, as format 1, 2 or 3 as described at
    https://en.wikipedia.org/wiki/ISO_8601#Time_intervals - or it can
    be on calendar-cli format (i.e. 2021-01-08 15:00:00+1h)
    """
    raise NotImplementedError()

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

def _set_attr_options(func):
    """
    decorator that will add options --set-categories, --set-description etc
    """
    for foo in attr_txt_one:
        func = click.option(f"--set-{foo}", help=f"Set ical attribute {foo}")(func)
    for foo in attr_txt_many:
        func = click.option(f"--set-{foo}", help=f"Set ical attribute {foo}", multiple=True)(func)
    return func

@cli.group()
@click.option('--all/--none', default=None, help='Select all (or none) of the objects.  Overrides all other selection options.')
@click.option('--uid', multiple=True, help='select an object with a given uid (or select more object with given uids)')
@click.option('--abort-on-missing-uid/--ignore-missing-uid', default=False, help='Abort if (one or more) uids are not found (default: silently ignore missing uids)')
@click.pass_context
def select(ctx, all, uid, abort_on_missing_uid, **kwargs):
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
            objs.append(c.objects)

    ## uid(s)
    missing_uids = []
    for uid_ in uid:
        cnt = 0
        for c in ctx.obj['calendars']:
            try:
                objs.append(c.object_by_uid(uid_))
                cnt += 1
            except caldav.error.NotFoundError:
                pass
        if not cnt:
            missing_uids.append(uid_)
    if abort_on_missing_uid and missing_uids:
        raise click.Abort(f"Did not find the following uids in any calendars: {missing_uids}")

@select.command()
@click.pass_context
def list(ctx, **kwargs):
    """
    print out a list of tasks/events/journals
    """
    raise NotImplementedError()

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
        raise click.Abort(f"Not going to delete {len(objs)} items")
    for obj in objs:
        obj.delete()

@select.command()
@click.pass_context
def complete(ctx, **kwargs):
    raise NotImplementedError()

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
@_set_attr_options
@click.pass_context
def add(ctx, **kwargs):
    """
    Save new objects on calendar(s)
    """
    if len(ctx.obj['calendars'])>1 and kwargs['multi_add'] is False:
        raise click.Abort("Giving up: Multiple calendars given, but --no-multi-add is given")
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
            raise click.Abort("Giving up: Multiple calendars found/given, please specify which calendar you want to use")

    ctx.obj['ical_fragment'] = "\n".join(kwargs['add_ical_line'])
    ctx.obj['add_args'] = {}
    for x in kwargs:
        if x.startswith('set_'):
            ctx.obj['add_args'][x[4:]] = kwargs[x]

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

@add.command()
@click.argument('summary', nargs=-1)
@click.pass_context
def todo(ctx, summary):
    """
    Creates a new task with given SUMMARY

    Examples: 

    kal add todo "fix all known bugs in calendar-cli"
    kal add todo --set-due=2050-12-10 "release calendar-cli version 42.0.0"
    """
    summary = " ".join(summary)
    ctx.obj['add_args']['summary'] = (ctx.obj['add_args']['summary'] or '') + summary
    if not ctx.obj['add_args']['summary']:
        raise click.Abort("denying to add a TODO with no summary given")
        return
    for cal in ctx.obj['calendars']:
        todo = cal.save_todo(ical=ctx.obj['ical_fragment'], **ctx.obj['add_args'], no_overwrite=True)
        click.echo(f"uid={todo.id}")

@add.command()
## TODO
@click.argument('summary')
@click.argument('timespec')
@click.pass_context
def event(ctx, summary, timespec):
    """
    Creates a new event with given SUMMARY at the time specifed through TIMESPEC.

    TIMESPEC is an ISO-formatted date or timestamp, optionally with a postfixed interval
.
    Examples:

    kal add event "final bughunting session" 2004-11-25+5d
    kal add event "release party" 2004-11-30T19:00+2h
    """
    for cal in ctx.obj['calendars']:
        (dtstart, dtend) = _parse_timespec(timespec)
        #event = cal.add_event(
        click.echo(f"uid={uid}")

def journal():
    click.echo("soon you should be able to add journal entries to your calendar")
    raise NotImplementedError("foo")

if __name__ == '__main__':
    cli()
