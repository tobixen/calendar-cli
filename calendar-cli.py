#!/usr/bin/python2.7

## (the icalendar library is not ported to python3?)

import argparse
import pytz
from datetime import datetime, timedelta
import dateutil.parser
from icalendar import Calendar,Event

__version__ = "0.01"
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

def calendar_add(args):
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
    #event.add('uid', uid)
    event.add('summary', ' '.join(args.description))
    cal.add_component(event)
    return cal

parser = argparse.ArgumentParser()

## Global options
parser.add_argument("--icalendar", help="Do not connect to CalDAV server, but read/write icalendar format from stdin/stdout", action="store_true")
parser.add_argument("--timezone", help="Timezone to use")
parser.add_argument('--language', help="language used", default="EN")

## TODO: check sys.argv[0] to find command
subparsers = parser.add_subparsers(title='command')

calendar_parser = subparsers.add_parser('calendar')
calendar_subparsers = calendar_parser.add_subparsers(title='subcommand')
calendar_add_parser = calendar_subparsers.add_parser('add')
calendar_add_parser.add_argument('event_time', help="Timestamp and duration of the event.  See the documentation for event_time specifications")
calendar_add_parser.add_argument('description', nargs='+')
calendar_add_parser.set_defaults(func=calendar_add)

calendar_agenda_parser = calendar_subparsers.add_parser('agenda')
calendar_agenda_parser.set_defaults(func=niy)
todo_parser = subparsers.add_parser('todo')
todo_parser.set_defaults(func=niy)
args = parser.parse_args()
ret = args.func(args)

if args.icalendar:
    print(ret.to_ical())
else:
    nyi()

