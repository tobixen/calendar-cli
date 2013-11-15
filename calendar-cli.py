#!/usr/bin/python2.7

## (the icalendar library is not ported to python3?)

import argparse
import urlparse
import pytz
from datetime import datetime, timedelta
import dateutil.parser
from icalendar import Calendar,Event
from caldavclientlibrary.client.account import CalDAVAccount
from caldavclientlibrary.protocol.url import URL
import uuid
import json
import os
import logging

__version__ = "0.04"
__author__ = "Tobias Brox"
__author_short__ = "tobixen"
__copyright__ = "Copyright 2013, Tobias Brox"
#__credits__ = []
__license__ = "GPL"
__maintainer__ = "Tobias Brox"
__email__ = "t-calendar-cli@tobixen.no"
__status__ = "Development"
__product__ = "calendar-cli"

def niy(*args, **kwargs):
    if 'feature' in kwargs:
        raise NotImplementedError("This feature is not implemented yet: %(feature)s" % kwargs)
    raise NotImplementedError

def caldav_connect(args):
    # Create the account
    splits = urlparse.urlsplit(args.caldav_url)
    ssl = (splits.scheme == "https")
    return CalDAVAccount(splits.netloc, ssl=ssl, user=args.caldav_user, pswd=args.caldav_pass, root=(splits.path or '/'), principal=None, logging=args.debug_logging)

def find_calendar_url(caldav_conn, args):
    if args.calendar_url:
        splits = urlparse.urlsplit(args.calendar_url)
        if splits.path.startswith('/') or splits.scheme:
            ## assume fully qualified URL or absolute path
            url = args.calendar_url
        else:
            ## assume relative path
            url = args.caldav_url + args.calendar_url
    else:
        ## Find default calendar
        url = caldav_conn.getPrincipal().listCalendars()[0].path

    ## Unique file name
    if not url.endswith('/'):
        url += '/'
    return url


def calendar_add(caldav_conn, args):
    cal = Calendar()
    cal.add('prodid', '-//{author_short}//{product}//{language}'.format(author_short=__author_short__, product=__product__, language=args.language))
    cal.add('version', '2.0')
    if args.timezone:
        tz = pytz.timezone(args.timezone)
    event = Event()
    ## read timestamps from arguments
    dtstart = dateutil.parser.parse(args.event_time)
    event.add('dtstart', dtstart)
    ## TODO: handle duration and end-time as options.  default 3600s by now.
    event.add('dtend', dtstart + timedelta(0,3600))
    ## not really correct, and it breaks i.e. with google calendar
    #event.add('dtstamp', datetime.now())
    ## maybe we should generate some uid?
    uid = uuid.uuid1()
    event.add('uid', str(uid))
    event.add('summary', ' '.join(args.description))
    cal.add_component(event)

    if args.icalendar and args.nocaldav:
        print(cal.to_ical())
        return
    if args.icalendar or args.nocaldav:
        raise ValueError("Nothing to do/invalid option combination for 'calendar add'-mode; either both --icalendar and --nocaldav should be set, or none of them")
        return
    
    url = URL(find_calendar_url(caldav_conn, args) + str(uid) + '.ics')
    caldav_conn.session.writeData(url, cal.to_ical(), 'text/calendar', method='PUT')

def calendar_agenda(caldav_conn, args):
    if args.nocaldav and args.icalendar:
        niy(feature="Read events from stdin in ical format")

    if args.nocaldav:
        raise ValueError("Agenda with --nocaldav only makes sense together with --icalendar")

    dtstart = dateutil.parser.parse(args.from_time)
    if args.to_time:
        dtend = dateutil.parser.parse(args.to_time)
    else:
        dtend = dtstart + timedelta(1,0)
    ## TODO: time zone
    ## No need with "expand" - as for now the method below throws away the expanded data :-(  We get a list of URLs, and then we need to do a get on each and one of them ...
    collection = caldav_conn.session.queryCollection(URL(find_calendar_url(caldav_conn, args)), timerange=True, start=dtstart.strftime("%FT%H%M%S"), end=dtend.strftime("%FT%H%M%S"), expand=False)
    ret_ical = []
    for url in collection:
        ret_ical.append(caldav_conn.session.readData(url))
    if args.icalendar:
        for ical in ret_ical:
            print ical
    else:
        import pdb; pdb.set_trace()
        ret_ical = [Calendar.from_ical(c[0]) for c in ret_ical]
        niy("parse calendar events and print them in a nice format")

def main():
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
    args, remaining_argv = conf_parser.parse_known_args()

    config = {}
    try:
        with open(args.config_file) as config_file:
            config = json.load(config_file)
    except IOError:
        ## File not found
        logging.info("no config file found")
    except ValueError:
        logging.error("error in config file", exc_info=True)
        raise

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

    ## TODO: check sys.argv[0] to find command
    ## TODO: set up logging
    subparsers = parser.add_subparsers(title='command')

    calendar_parser = subparsers.add_parser('calendar')
    calendar_parser.add_argument("--calendar-url", help="URL for calendar to be used (may be absolute or relative to caldav URL)")
    calendar_subparsers = calendar_parser.add_subparsers(title='subcommand')
    calendar_add_parser = calendar_subparsers.add_parser('add')
    calendar_add_parser.add_argument('event_time', help="Timestamp and duration of the event.  See the documentation for event_time specifications")
    calendar_add_parser.add_argument('description', nargs='+')
    calendar_add_parser.set_defaults(func=calendar_add)

    calendar_agenda_parser = calendar_subparsers.add_parser('agenda')
    calendar_agenda_parser.add_argument('from_time', help="Fetch calendar events from this timestamp.  See the documentation for time specifications")
    calendar_agenda_parser.add_argument('--to-time', help="Fetch calendar until this timestamp")
    calendar_agenda_parser.set_defaults(func=calendar_agenda)

    todo_parser = subparsers.add_parser('todo')
    todo_parser.set_defaults(func=niy)
    args = parser.parse_args(remaining_argv)

    if not args.nocaldav:
        caldav_conn = caldav_connect(args)

    ret = args.func(caldav_conn, args)

if __name__ == '__main__':
    main()
