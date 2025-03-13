#!/usr/bin/env bash

storage=$(mktemp -d)

echo "This script will attempt to set up a Radicale server and a Xandikos server and run the test code towards those two servers"
echo "The test code itself is found in tests.sh"

export RUNTESTSNOPAUSE="foo"

echo "########################################################################"
echo "## RADICALE"
echo "########################################################################"
python3 -m radicale --storage-filesystem-folder="$storage" &
radicale_pid=$!
sleep 0.3
if [ -n "$radicale_pid" ]; then
    echo "## Radicale now running on pid $radicale_pid"
    calendar_cli="$( printf "%s%s%s%s" '../bin/calendar-cli.py ' \
        '--caldav-url=http://localhost:5232/ --caldav-pass=password1 ' \
        '--caldav-user=testuser ' \
        '--calendar-url=/testuser/calendar-cli-test-calendar' )"
    echo "## Creating a calendar"
    $calendar_cli calendar create calendar-cli-test-calendar

    ## crazy, now I get a 403 forbidden on the calendar create, but
    ## the calendar is created.  Without the statement above, I'll
    ## just get 404 when running tests.
    export calendar_cli
    if [ -n "$DEBUG" ]; then
        echo "press enter to run tests"
        read -r
    fi
    ./tests.sh
    if [ -n "$DEBUG" ]; then
        echo "press enter to take down test server"
        read -r
    fi
    kill "$radicale_pid"
    sleep 0.3
else
    echo "## Could not start up radicale (is it installed?).  Will skip running tests towards radicale"
fi


echo "########################################################################"
echo "## XANDIKOS"
echo "########################################################################"
xandikos_bin=$(which xandikos 2> /dev/null)
if [ -n "$xandikos_bin" ]; then
    $xandikos_bin --defaults -d "$storage" &
    xandikos_pid=$!
    sleep 0.5
fi

if [ -n "$xandikos_pid" ]; then
    echo "## Xandikos now running on pid $xandikos_pid"
    calendar_cli="../bin/calendar-cli --caldav-url=http://localhost:8080/ --caldav-user=user"
    export calendar_cli
    ./tests.sh
    kill "$xandikos_pid"
else
    echo "## Could not start up xandikos (is it installed?).  Will skip running tests towards xandikos"
fi


echo "########################################################################"
echo "## cleanup"
echo "########################################################################"
rm -rf "$storage"
