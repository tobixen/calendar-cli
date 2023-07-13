import pytest
import sys
sys.path.insert(0,'.')
sys.path.insert(1,'..')
from datetime import datetime, date
from calendar_cli.template import Template

"""calendar-cli is a command line utility, and it's an explicit design
goal that it should contain minimal logic except for parsing and
passing command line options and parameters to the caldav library and
printing output from the caldav library.  Functional tests verifying
that the tool actually works as intended is done through shell
scripts, and can be run through test_calendar-cli.sh.  There is no
goal to get complete code coverage through this unit test, though any
"extra" logic except for simple passing of options and parameters to
the caldav library ought to be tested here.  """

class TestTemplate:
    def setup_method(self):
        self.date = date(1990, 10, 10)
        
    def test_formatting_with_timespec(self):
        template=Template("This is an ISO date: {date:%F}")
        text = template.format(date=self.date)
        assert text == "This is an ISO date: 1990-10-10"

        text = template.format(foo=self.date)
        assert text == "This is an ISO date: "
        
    def test_formatting_with_simple_default(self):
        template=Template("This is an ISO date: {date:?(date is missing)?%F}")
        text = template.format(date=self.date)
        assert text == "This is an ISO date: 1990-10-10"

        text = template.format(foo=self.date)
        assert text == "This is an ISO date: (date is missing)"

    def test_subvalue_with_default(self):
        template = Template("This is a year: {date.year:?NA?>5}")
        text = template.format(date=self.date)
        assert text == "This is a year:  1990"
        text = template.format(foo=self.date)
        assert text == "This is a year:    NA"

    def test_missing_replaced_with_advanced_default(self):
        template = Template("Date is maybe {date:?{foo}?%F}")
        text = template.format(date=self.date)
        assert text == "Date is maybe 1990-10-10"
        text = template.format(foo=self.date)
        assert text == "Date is maybe 1990-10-10"
        text = template.format(foo=self.date, date=self.date)
        assert text == "Date is maybe 1990-10-10"

    def test_missing_replaced_with_even_more_advanced_default(self):
        template = Template("Date is maybe {date:?{foo:?bar?}?%F}")
        text = template.format(date=self.date)
        assert text == "Date is maybe 1990-10-10"
        text = template.format(foo=self.date)
        assert text == "Date is maybe 1990-10-10"
        text = template.format(foo=self.date, date=self.date)
        assert text == "Date is maybe 1990-10-10"
        text = template.format()
        assert text == "Date is maybe bar"
