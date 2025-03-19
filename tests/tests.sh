#!/usr/bin/env bash

set -e

if [ "$1" ]; then
    calendar_cli="$*"
fi

########################################################################
## SETUP
########################################################################

for path in . .. ./tests ../tests; do
    setup="$path/_setup_alias"
    if [ -f $setup ]; then
        source $setup
        test_init
        [ "$calendar_cli" ] || calendar_cli="$( find_executable_to_test )"
    fi
done
set_test_command "$calendar_cli"

if [ -z "$RUNTESTSNOPAUSE" ]; then
    echo "tests.sh"
    echo
    echo "Generally, tests.sh should only be run directly if you know what you are doing"
    echo "You may want to use test_calendar-cli.sh instead"
    echo
    echo "This script will use the following commands to access a calendar server:"
    echo
    echo "$calendar_cli"
    echo
    echo "This may work if you have configured a calendar server."
    echo "The tests will add and delete events and tasks."
    echo "Content from 2010-10 may be deleted"
    echo
    echo "Press enter or ctrl-C"
    read -r
fi


echo "## CLEANUP from earlier failed test runs, if any"

export QUIET=true
for uid in $(
    $calendar_cli calendar agenda --from-time=2010-10-09 --agenda-days=5 \
        --event-template='{uid}')
do
    $calendar_cli calendar delete --event-uid="$uid"
done
$calendar_cli todo --categories scripttest delete
unset QUIET

########################################################################
## TEST CODE FOLLOWS
########################################################################

echo "## EVENTS"

echo "## testing $calendar_cli"
echo "## this is a very simple test script without advanced error handling"
echo "## if this test script doesn't output 'ALL TESTS COMPLETED!  YAY!' in the end, something went wrong"

echo "## Attempting to add an event at 2010-10-09 20:00:00, 2 hours duration"
calendar_cli calendar add '2010-10-09 20:00:00+2h' 'testing testing'
uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid" ] || error "got no UID back"

echo "## Attempting to add an event at 2010-10-10 20:00:00, CET (1 hour duration is default), with description and non-ascii location"
calendar_cli calendar add '2010-10-10 20:00:00+01:00' 'testing testing' --set-description='this is a test calendar event' --set-location='Москва'
uid2=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid2" ] || error "got no UID back"

echo "## Attempting to add an event at 2010-10-11 20:00:00, CET, 3h duration"
calendar_cli calendar add '2010-10-11 20:00:00+01:00+3h' 'testing testing'
uid3=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
echo "## OK: Added the event, uid is $uid"

echo "## Taking out the agenda for 2010-10-09 + four days"
calendar_cli calendar agenda --from-time=2010-10-09 --agenda-days=4 --event-template='{description} {location}'
echo $__test_output | { grep -q 'this is a test calendar event Москва' && echo "## OK: found the event" ; } || error "didn't find the event"

echo "## Taking out the agenda for 2010-10-10, with uid"
calendar_cli calendar agenda --from-time=2010-10-10 --agenda-days=1 --event-template='{dtstart} {uid}'
echo $__test_output | { grep -q $uid2 && echo "## OK: found the UID" ; } || error "didn't find the UID"

echo "## Deleting events with uid $uid $uid2 $uid3"
calendar_cli calendar delete --event-uid=$uid
calendar_cli calendar delete --event-uid=$uid2
calendar_cli calendar delete --event-uid=$uid3

echo "## Searching again for the deleted event"
calendar_cli calendar agenda --from-time=2010-10-10 --agenda-days=3
echo $__test_output | { grep -q 'testing testing' && error "still found the event" ; } || echo "## OK: didn't find the event"

echo "## Adding a full day event"
calendar_cli calendar add --whole-day '2010-10-10+4d' 'whole day testing'
uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid" ] || error "got no UID back"

echo "## fetching the full day event, in ics format"
calendar_cli  --icalendar calendar agenda --from-time=2010-10-13 --agenda-days=1

echo "$__test_output" | grep -q "whole day" || error "could not find the event"
echo "$__test_output" | grep -q "20101010" || error "could not find the date"
echo "$__test_output" | grep -q "20101010T" && error "a supposed whole day event was found to be with the time of day"
echo "OK: found the event"

echo "## cleanup, delete it"
calendar_cli calendar delete --event-uid=$uid

## TODO - procrastinated, waiting for response on https://github.com/dateutil/dateutil/issues/1184
#uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
#[ -n "$uid" ] || error "got no UID back"
#calendar_cli  --icalendar calendar agenda --from-time=2010-10-13 --agenda-days=1
#echo "$__test_output" | grep -q "whole day" || error "could not find the event"
#echo "$__test_output" | grep -q "20101010" || error "could not find the date"
#echo "$__test_output" | grep -q "20101010T" && error "a supposed whole day event was found to be with the time of day"
#echo "OK: found the event"
#echo "## cleanup, delete it"
#calendar_cli calendar delete --event-uid=$uid

echo "## A full day event should be implicit when giving dates rather than timestamps"
calendar_cli calendar add '2010-10-10+3d' 'whole day testing'
uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid" ] || error "got no UID back"

echo "## fetching the full day event, in ics format"
calendar_cli  --icalendar calendar agenda --from-time=2010-10-12 --agenda-days=1

echo "$__test_output" | grep -q "whole day" || error "could not find the event"
echo "$__test_output" | grep -q "20101010" || error "could not find the date"
echo "$__test_output" | grep -q "20101010T" && error "a supposed whole day event was found to be with the time of day"
echo "OK: found the event"

echo "## cleanup, delete it"
calendar_cli calendar delete --event-uid=$uid

echo "## testing timezone support"
echo "## Create a UTC event"
calendar_cli --timezone='UTC' calendar add '2010-10-09 12:00:00+10m' 'testevent with a UTC timezone'
uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid" ] || error "got no UID back"

echo "## fetching the UTC-event, as ical data"
calendar_cli --icalendar --timezone=UTC calendar agenda --from-time='2010-10-09 11:59' --agenda-mins=3
[ -n "$__test_output" ] || error "failed to find the event that was just added"
echo "$__test_output" | grep -q "20101009T120000Z" || error "failed to find the UTC timestamp.  Perhaps the server is yielding timezone data for the UTC timezone?  In that case, the assert in the test code should be adjusted"

echo "## cleanup, delete it"
calendar_cli calendar delete --event-uid=$uid

echo "## Create an event with a somewhat remote time zone, west of UTC"
calendar_cli --timezone='Brazil/DeNoronha' calendar add '2010-10-09 12:00:00+10m' 'testevent with a time zone west of UTC'
uid=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
[ -n "$uid" ] || error "got no UID back"

echo "## fetching the remote time zone event, as ical data"
calendar_cli --icalendar --timezone=UTC calendar agenda --from-time='2010-10-09 13:59' --agenda-mins=3
## zimbra changes Brazil/DeNoronha to America/Noronha.  Actually, the server may theoretically use arbitrary IDs for the timezones.
echo "$__test_output" | grep -Eq "TZID=\"?[a-zA-Z/]*Noronha" || echo "$__test_output" | grep -q "140000Z" ||
    error "failed to find the remote timezone"

echo "## fetching the remote time zone event, in UTC-time"
calendar_cli --timezone=UTC calendar agenda --from-time='2010-10-09 13:59' --agenda-mins=3 --event-template='{dtstart}'
[ "$__test_output" == '2010-10-09 14:00 (Sat)' ] || error "expected dtstart to be 2010-10-09 14:00 (Sat)"

echo "## fetching the remote time zone event, in CET-time (UTC+2 with DST, and October is defined as summer in Oslo, weird)"
calendar_cli --timezone=Europe/Oslo calendar agenda --from-time='2010-10-09 15:59' --agenda-mins=3 --event-template='{dtstart}'
[ "$__test_output" == '2010-10-09 16:00 (Sat)' ] || error "expected dtstart to be 2010-10-09 15:00 (Sat)"

echo "## cleanup, delete it"
calendar_cli calendar delete --event-uid=$uid

echo "## TODOS / TASK LISTS"

echo "## Attempting to add a task with category 'scripttest'"
calendar_cli todo add --set-categories scripttest "edit this task"
uidtodo1=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
calendar_cli todo add --set-categories scripttest todo "edit this task2"
uidtodo2=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')

echo "## Listing out all tasks with category set to 'scripttest'"
calendar_cli todo --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 2 ] || error "We found more or less or none of the two todo items we just added"

echo "## Editing the task"
calendar_cli todo --categories scripttest edit --set-summary "editing" --add-categories "scripttest2"

echo "## Verifying that the edits got through"
calendar_cli todo --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found the todo item we just edited and nothing more"
calendar_cli todo --categories scripttest2 list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found the todo item we just edited and nothing more"
calendar_cli todo --comment editing list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found the todo item we just edited and nothing more"

echo "## Complete the task"
calendar_cli todo --categories scripttest complete
calendar_cli todo --categories scripttest list
[ -z "$__test_output" ] && echo "## OK: todo-item is done"
calendar_cli todo --todo-uid $uidtodo1 delete

## parent-child relationships
echo "## Going to add three todo-items with children/parent relationships"
calendar_cli todo add --set-categories scripttest "this is a grandparent"
uidtodo2=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
calendar_cli todo --categories=scripttest add --set-categories scripttest --is-child "this is a parent and a child"
uidtodo3=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
calendar_cli todo --categories=scripttest add --set-categories scripttest --is-child "this task has two parents"
uidtodo4=$(echo $__test_output | perl -ne '/uid=(.*)$/ && print $1')
calendar_cli todo --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 3 ] && echo "## OK: found three tasks"
calendar_cli todo --hide-parents --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found only one task now"
echo "## Going to complete the children task"
calendar_cli todo --hide-parents --categories scripttest complete
calendar_cli todo --hide-parents --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found only one task now"
calendar_cli todo --hide-parents --categories scripttest complete
calendar_cli todo --hide-parents --categories scripttest list
[ $(echo "$__test_output" | wc -l) == 1 ] && echo "## OK: found only one task now"
calendar_cli todo --hide-parents --categories scripttest complete
calendar_cli todo --hide-parents --categories scripttest list
[ -z "$__test_output" ] && echo "## OK: found no tasks now"

echo "## ALL TESTS COMPLETED!  YAY!"


rm $__test_outfile

