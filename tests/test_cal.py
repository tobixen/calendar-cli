import pytest
import sys
sys.path.insert(0,'.')
sys.path.insert(1,'..')
from datetime import datetime, date
from cal import parse_timespec
from lib.template import Template

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
    def setup(self):
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

class TestParseTimestamp:
    def _testTimeSpec(self, expected):
        for input in expected:
            assert parse_timespec(input) == expected[input]

    @pytest.mark.skip(reason="Not implemented yet, waiting for feedback on https://github.com/gweis/isodate/issues/77")
    def testIsoIntervals(self):
        raise pytest.SkipTest("")
        expected = {
            "2007-03-01T13:00:00Z/2008-05-11T15:30:00Z":
                (datetime(2007,3,1,13), datetime(2008,5,11,15,30)),
            "2007-03-01T13:00:00Z/P1Y2M10DT2H30M":
                (datetime(2007,3,1,13), datetime(2008,5,11,15,30)),
            "P1Y2M10DT2H30M/2008-05-11T15:30:00Z":
                (datetime(2007,3,1,13), datetime(2008,5,11,15,30))
        }
        self._testTimeSpec(expected)

    def testOneTimestamp(self):
        expected = {
            "2007-03-01T13:00:00":
                (datetime(2007,3,1,13), None),
            "2007-03-01 13:00:00":
                (datetime(2007,3,1,13), None),
        }
        self._testTimeSpec(expected)
        
    def testOneDate(self):
        expected = {
            "2007-03-01":
                (date(2007,3,1), None)
        }
        self._testTimeSpec(expected)
        
    def testTwoTimestamps(self):
        expected = {
            "2007-03-01T13:00:00 2007-03-11T13:30:00":
                (datetime(2007,3,1,13), datetime(2007,3,11,13,30)),
            "2007-03-01 13:00:00 2007-03-11 13:30:00":
                (datetime(2007,3,1,13), datetime(2007,3,11,13,30)),
        }
        self._testTimeSpec(expected)

    def testTwoDates(self):
        expected = {
            "2007-03-01 2007-03-11":
                (date(2007,3,1), date(2007,3,11))
        }
        self._testTimeSpec(expected)

    def testCalendarCliFormat(self):
        expected = {
            "2007-03-01T13:00:00+10d":
                (datetime(2007,3,1,13), datetime(2007,3,11,13)),
            "2007-03-01T13:00:00+2h":
                (datetime(2007,3,1,13), datetime(2007,3,1,15)),
            "2007-03-01T13:00:00+2.5h":
                (datetime(2007,3,1,13), datetime(2007,3,1,15,30)),
            "2007-03-01T13:00:00+2h30m":
                (datetime(2007,3,1,13), datetime(2007,3,1,15,30)),
            "2007-03-01+10d":
                (date(2007,3,1), date(2007,3,11))
        }
        self._testTimeSpec(expected)

        
