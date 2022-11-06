"""String formatter that allows default values to be passed in the
template string.

This does not really belong in the calendar-cli package.  I was
googling a bit, and didn't find anything like this out there ... but
I'm sure there must exist something like this?"""

import datetime
import string
import re

class NoValue():
    def __getattr__(self, attr):
        return self
    def __getitem__(self, attr):
        return self
    def __str__(self):
        return ""
    def __format__(self, spec):
        try:
            return "".__format__(spec)
        except:
            return ""

no_value = NoValue()

class Template(string.Formatter):
    def __init__(self, template):
        self.template = template

    def format(self, *pargs, **kwargs):
        return super().format(self.template, *pargs, **kwargs)
    
    def get_value(self, key, args, kwds):
        try:
            return string.Formatter.get_value(self, key, args, kwds)
        except:
            return no_value

    def format_field(self, value, format_spec):
        rx = re.match(r'\?([^\?]*)\?(.*)', format_spec)
        if rx:
            format_spec = rx.group(2)
            if value is no_value:
                value = rx.group(1)
        try:
            return string.Formatter.format_field(self, value, format_spec)
        except:
            return string.Formatter.format_field(self, value, "")
