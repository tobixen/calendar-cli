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

## TODO ...
def _parse_timespec(timespec):
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

attr_txt_one = ['location', 'description', 'geo', 'organizer', 'summary']
attr_txt_many = ['categories', 'comment', 'contact', 'resources']

def set_attr_options(func):
    for foo in attr_txt_one:
        func = click.option()

@cli.group()
@click.option('-l', '--add-ical-line', multiple=True, help="extra ical data to be injected")
@click.option('--multi-add/--no-multi-add', default=False, help="Add things to multiple calendars")
@click.option('--first-calendar/--no-first-calendar', default=False, help="Add things to the first given calendar")
@click.pass_context
def add(ctx, **kwargs):
    if (len(ctx.obj['calendars'])>1 and
        not kwargs['multi_add'] and
        not click.confirm(f"Multiple calendars given.  Do you want to duplicate to {len(ctx.obj['calendars'])} calendars? (tip: use option --multi-add to avoid this prompt in the future)")):
        calendar = ctx.obj['calendars'][0]
        ## TODO: we need to make sure f"{calendar.name}" will always work or something
        if (kwargs['first_calendar'] or
            click.confirm(f"First calendar on the list has url {calendar.url} - should we add there? (tip: use --calendar-url={calendar.url} or --first_calendar to avoid this prompt in the future)")):
            ctx.obj['calendars'] = [ calendar ]
        else:
            raise click.Abort()
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

@add.command()
def todo():
    click.echo("soon you should be able to add tasks to your calendar")
    raise NotImplementedError("foo")

@add.command()
## TODO
@click.argument('description')
@click.argument('timespec')
@click.pass_context
def event(ctx, description, timespec):
    """
    Creates a new event with given DESCRIPTION at the time specifed through TIMESPEC.

    TIMESPEC is an ISO-formatted date or timestamp, optionally with a postfixed interval.

    Examples: 

    kal add event "final bughunting session" 2004-11-25+5d
    kal add event "release party" 2004-11-30T19:00+2h
    """
    for cal in ctx['calendars']:
        (dtstart, dtend) = _parse_timespec(timespec)
        #event = cal.add_event(
        click.echo(uid)

def journal():
    click.echo("soon you should be able to add journal entries to your calendar")
    raise NotImplementedError("foo")

if __name__ == '__main__':
    cli()
