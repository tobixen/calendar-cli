#!/bin/bash

storage=$(mktemp -d)

echo "########################################################################"
echo "## RADICALE"
echo "########################################################################"
python3 -m radicale --storage-filesystem-folder=$storage &
sleep 0.3
radicale_pid=$(jobs -l | perl -ne '/^\[\d+\]\+\s+(\d+)\s+Running/ && print $1')
if [ -n "$radicale_pid" ]
then
    echo "## Radicale now running on pid $radicale_pid"
    calendar_cli="../calendar-cli --caldav-url=http://localhost:5232/ --caldav-user=testuser --calendar-url=/testuser/calendar-cli-test-calendar"
    echo "## Creating a calendar"
    $calendar_cli calendar create calendar-cli-test-calendar
    
    ## crazy, now I get a 403 forbidden on the calendar create, but
    ## the calendar is created.  Without the statement above, I'll
    ## just get 404 when running tests.
    export calendar_cli
    ./tests.sh
    kill $radicale_pid
    sleep 0.3
else
    echo "## Could not start up radicale (is it installed?).  Will skip running tests towards radicale"
fi


echo "########################################################################"
echo "## XANDIKOS"
echo "########################################################################"
echo "Not supported at the moment (xandikos dev decided to return a 500 telling that expand doesn't work when I prodded them that it didn't work.  should maybe try to create a workaround)"
exit 0
xandikos_bin=$(which xandikos 2> /dev/null)
if [ -n "$xandikos_bin" ] 
then
    $xandikos_bin --defaults -d $storage &
    sleep 0.5
    xandikos_pid=$(jobs -l | perl -ne '/^\[\d+\]\+\s+(\d+)\s+Running/ && print $1')
fi

if [ -n "$xandikos_pid" ]
then
    echo "## Xandikos now running on pid $xandikos_pid"
    calendar_cli="../calendar-cli --caldav-url=http://localhost:8080/ --caldav-user=user"
    export calendar_cli
    ./tests.sh
    kill $xandikos_pid
else
    echo "## Could not start up xandikos (is it installed?).  Will skip running tests towards xandikos"
fi


echo "########################################################################"
echo "## cleanup"
echo "########################################################################"
rm -rf $storage
