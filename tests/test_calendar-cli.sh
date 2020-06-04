#!/bin/bash

########################################################################
## RADICALE
########################################################################
storage=$(mktemp -d)
python3 -m radicale --storage-filesystem-folder=$storage &
sleep 0.3
jobs -l
radicale_pid=$(jobs -l | perl -ne '/^\[\d+\]\+\s+(\d+)\s+Running/ && print $1')
if [ -n "$radicale_pid" ]
then
    echo "## Radicale now running on pid $radicale_pid"
    calendar_cli="../calendar-cli --caldav-url=http://localhost:5232/ --caldav-user=testuser --calendar-url=/testuser/calendar-cli-test-calendar"
    $calendar_cli calendar create calendar-cli-test-calendar
    export calendar_cli
    ./tests.sh
    kill $radicale_pid
    rm -rf $storage
else
    echo "## Could not start up radicale (is it installed?).  Will skip running tests towards radicale"
fi


########################################################################
## XANDIKOS
########################################################################
## TODO!  work in progress

