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

__version__ = "0.03"
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
    raise NotImplementedError

def caldav_connect(args):
    # Create the account
    splits = urlparse.urlsplit(args.caldav_url)
    ssl = (splits.scheme == "https")
    return CalDAVAccount(splits.netloc, ssl=ssl, user=args.caldav_user, pswd=args.caldav_pass, root=(splits.path or '/'), principal=None, logging=args.debug_logging)


def calendar_add(caldav_conn, args):
    if (not args.calendar_url):
        ## args.calendar_url must be given ... :/
        niy()

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

    if args.icalendar:
        print(cal.to_ical())
    elif args.caldav_url:
        caldav_conn.session.writeData(URL(args.calendar_url+str(uid)+'.ics'), cal.to_ical(), 'text/calendar', method='PUT')

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
    parser.add_argument("--icalendar", help="Do not connect to CalDAV server, but read/write icalendar format from stdin/stdout", action="store_true")
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
    calendar_parser.add_argument("--calendar-url", help="URL for calendar to be used")
    calendar_subparsers = calendar_parser.add_subparsers(title='subcommand')
    calendar_add_parser = calendar_subparsers.add_parser('add')
    calendar_add_parser.add_argument('event_time', help="Timestamp and duration of the event.  See the documentation for event_time specifications")
    calendar_add_parser.add_argument('description', nargs='+')
    calendar_add_parser.set_defaults(func=calendar_add)

    calendar_agenda_parser = calendar_subparsers.add_parser('agenda')
    calendar_agenda_parser.set_defaults(func=niy)
    todo_parser = subparsers.add_parser('todo')
    todo_parser.set_defaults(func=niy)
    args = parser.parse_args(remaining_argv)

    if not args.icalendar:
        caldav_conn = caldav_connect(args)

    ret = args.func(caldav_conn, args)

if __name__ == '__main__':
    main()
