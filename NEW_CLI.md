I'm currently working on a cal.py aka kal that eventually will replace calendar-cli.py.  This is the long document with design thoughts, and it may not be completely in sync with what I'm actually implementing.  You may want to read the shorter [USER_GUIDE](USER_GUIDE.md) for a more up-to-date and shorter document.

## General thoughts

* calendar-cli should be a simple command line wrapper over existing python libraries.  It should not contain a lot of logic besides parsing command line options and arguments.  Logic that may be useful for python programmers should be pushed to other libraries, like the caldav-library, or be split into a new library.
* Old calendar-cli stays for quite some time, for backward compatibility
* We'll split out a new command for the new interface, probably it will be `kal`. I considered a lot of different name options:
  * cal ... but `cal(1)` - is a well-established command, so it's out of the question (unless we overload the command by making a wrapper calling `cal` if no subcommand is given ... that could be an idea).
  * `calcli`, `cal-cli` and different variants of it.  The dash already hurt me with calendar-cli, don't want to repeat that.  And "cli" is a bit redundant, when typing a command on the command line it's reasonable to assume it's a cli.
  * `cal-add`, or even `cal-add-todo` ... but modern cli frameworks are more often than not built over different variants of `command subcommand subsubcommand`.
  * `kal` ... looks a bit like a silly misspelling or an attempt to localize it into some non-english language (which then will look even more silly when combined with english subcommands and english options). At the other hand, I do see that it's not entirely uncommon to use `klass` when putting a class into a variable in python, `kal` is short to type, easy to remember, and there aren't too many other projects utilizing the `kal`-name as far as I can see.
* We'll use click, which is supposed to support subcommands in an elegant way.
* I'm fairly happy with the todo interface for listing/editing/completing.  First options to filter/sort/limit the todo item(s), then a subcommand for what to do on those items.
* Should consider that we at some point may want to support tools that doesn't support caldav.  Should also consider that we may want to support tools that doesn't support icalendar.  For instance, issue tracking through gitlab or github.
* Perhaps a new calendar-tui for increased interactivity?
* Some or all of the commands should be possible to iterate over several calendars.  This is almost impossible with `calendar-cli` due to the way the configuration is made (perhaps we should require that connection parameters are given in a config file?)

## Details

### Add an event, task or journal entry:

```
kal --config-section=private_calendar add --set-location="Aker Brygge marina" event "new years party" 2032-12-31T20:00+5h 
kal add todo "Buy food for the new years party" --set-due=2032-12-30T20:00 --set-duration=1h

kal add journal "Captain's log" 2020-12-04 'Started from Świnoujście a bit after 03AM.  Due to miscommunication, bad planning and language problems my crew member Bartek managed to throw the whole mooring rope to the sea (clearly the captains fault - I didnt explain the task "release one end of the rope, let it go into the sea and then pull it in" well enough, and he did ask multiple times "are you really sure about that?" before throwing both ends of the rope to the sea).  Tail wind, between 8-16 knots relative windspeed, changed a bit between broad reach and butterfly.  While going butterfly, due to a rather big wave we had an accidental jib, bad enough that the preventer rope broke off the cleat it was attached to (but luckily no damanges to the rig).  There seems to be a minor salt water leakage by the rudder.  Passed Falsterbo around 21, moored up in the guest harbour in Skanör around 22.  Very quiet as it was way outside the season.  Didnt find any obvious choice on the payment automat for harbor fee - eventually I payed SEK 100 for "tvättstuga".  I got no access to the laundry room, so I decided that 100 SEK was an OK price for staying overnight with electricity off-season in Skanör.'
```

While the specification for journal, todo and event are fairly similar, the non-optional parameters will be different due to slightly different typical use-case scenarios:

* All three should have a summary as the mandatory first parameter (deviation from calendar-cli which takes the timestamp as first parameter when creating an event)
* For making todos, that should be the only mandatory parameter (as with "calendar-cli todo add").  Not all tasks have a clear due-date.  In accordance with my task management ideas above, all tasks should eventually have a due date set, but the idea is also to be able to quickly throw things on the list, and then consider an appropriate priority and due date later.
* dtstart is (If I read the rfc correctly) optional for all three classes, but it doesn't make much sense to have an event without a start time - and a journal entry should have a date.  For events, the same timestamp format is used as in the existing calendar-cli - duration can be piggybacked in the timestamp.  Change of parameter order, with "calendar-cli calendar add" the dtstart should come before the summary.  This to make "summary first" consistent for all three calendar object resource classes.
* For journal entries (as they are intended), it doesn't make much sense to add an entry without a description, so it's the mandatory second parameter.

The todo-item added above has both due timestamp and duration set, which is against the RFC.  It will be converted to dtstart and due before it's pushed to the calendar.

### Reading the calendar

To get things out from the calendar, one can use the kal agenda command:

```
kal agenda --config-section=private --config-section=work --agenda-days=30 --event-template="{dtstart} {summary} UID={uid}" --todo-template="{due} {summary} UID={uid}"
```

kal agenda should first print out all events starting or ending within the next 30 days, then all tasks with dtstart or due within the next 30 days.  (in my revised "task management" above, dtstart is defined as due minus estimated work time).  The tasks should be "smart sorted", according to the algorithm given in the "Task management" section above ("based on the ratio between duration and available time until due date").  It should accept several --config-section, take out all it can find from those config sections and sort the things afterwards.  Exceptions due to unreachable caldav servers or calendars not supporting tasks etc should be caught and presented nicely.

The kal agenda is to be considered a convenience-command, it is slightly redundant.  The output of the command should be considered to be for direct human consumption, no further processing of the output should be done.  The kal select command is the ultimate tool for a lot of things:

```
kal select --timespan=2021-12-01+2w list
kal select --todo --nocategories --list
kal select --todo --nocategories -1 edit --add-category=keyboard
kal select --todo --due-before=2021-12-01 --categories=keyboard --smart-sort list
kal select --todo --due-before=2021-12-01 --categories=keyboard --smart-sort -1 complete
kal select --uid=e71a6180-45a2-11ec-9605-fa163e7cfdd5 delete
kal select --due-before=2021-12-24T15:00 --categories=housework calculate-panic-time --work-factor=0.125
kal select --journal --dtstart-after=2021-10-01 --dtstart-before=2021-11-01 sum_hours
```

kal select should select objects based on some criterias and then perform some action (`list`, `edit`, `postpone`, `complete`, `delete`, `calculate-panic-time`, 'sum_hours' and some more - see further below) on the objects.

The technical differences between tasks, events and journal entries are small - kal select should basically work on all three of them unless `--todo`, `--event` or `--journal` is epxlicitly given.  If the action given does not match one or more of the objects selected (say, "completing" a journal does not make sense), the script should raise an exception before doing any modifications of the calendar.  `--offset` and `--limit` may be used to specify a handful of objects.  "-1" is shortform for "--limit 1", or typically "do this action with the top item at the list"

`--smart-sort` will give the above mentioned sort algorithm for tasks, and regular sorting by dtstart for events and journals.

The `calculate-panic-time` command will take out all planned events and todo items, count the duration of those and print out a timestamp for when you need to panic.  If it shows a timestamp in the past one should either PANIC!!! or procrastinate some tasks and cancel some events.  The command takes the `--work-factor` parameter which specifies how much of the time you will be able to concentrate on the selected tasks.  For instance, an "ordinary" parent having kids to take care of, a daytime job, plus the need for sleeping every night may perhaps in average be able to spend 3 hours a day - or 12.5% of the full day - on house work.

This should cover most regular needs for putting events on a calendar and managing tasks and todo-lists.  It does not cover "pinning" tasks to a calendar nor tracking time spent on tasks.  There may also be a need for a bit more interactivity.  Sending invites and replying to invites is also not covered.

Logical "and" should be assumed between filter selectors.  I feel uncomfortable with implementing support for paranthesis and logical operators, but there could probably be a --union parameter working as a "logical or", and some syntax should be made for the individual filters (but `--limit`, `--offset` and `--sort` should be processed after the union).  Perhaps `--categories=housework+gardenwork` should fetch everything with either "housework" or "gardenwork" as category, while `--categories=housework,kitchen` should fetch all housework to be done in the kitchen.  Or maybe `--categories=housework&gardenwork` and `--categories=housework|gardenwork` is less ambiguous.  It probably needs to be thought more through.

sum_hours will sum the duration of all objects.  For tasks and events in the future, it's supposed to be the amount of time "committed", for tasks and events in the past, it is supposed to be the amount of time actually worked.  (Time tracking is tricky, the icalendar standard does not really support it, and journal entries cannot have duration, but I'll get back to that).

### Pinning tasks to calendar

The `pin` subcommand will "pin" one or more todo-items to some specific time on the calendar.  Duration will be copied.  The tasks will be serialized.  If there are conflicting events in the same calendar, the tasks will be put after the conflicting events.  No checks will be done to ensure that the tasks ends up within ordinary working hours, outside the night hours or before the due date.  Or perhaps some sanity checks should be done ... it will be a lot of cleanup-work to be done if one accidentally forgets "-1" and adds some hundreds of items to the calendar ...

```kal select --todo --categories=housework --smart-sort --limit=3 pin '2021-12-02 16:00'```

### Time tracking

(see also [NEXT_LEVEL.md](NEXT_LEVEL.md))

The `complete` subcommand takes optional parameters `--spent=4h`,  `--log="I just hammered on the keyboard all until eventually all the unit tests finally passed.  yay!"`, `--start=2021-10-06T12:00` and `--end=2021-10-06T16:00`.

Rules:

* A new journal entry is created, and marked as the child of the completed task or event.
* Both events and tasks can be "completed".  If an event is "completed", it is implicit that time was spent, and time will be tracked even without any extra parameters.
* If a task was completed and it has a child event ("pinned task"), it is to be considered as if the child event was completed.
* For an "ordinary" task (one that isn't pinned), time will only be tracked if at least one of the four options above is given.  Meaning that if no such option was given, the rest of the logic is ignored.
* If all three time-related parameters are given, the duration should match dtend-dtstart, and this should be validated.
* If two of the three time-related parameters are given, the third will be calculated.
* If only `--spent` is given and it's an event, '--start' is considered to be the dtstart of the event, and `--end` can be calculated.
* If only `--spent` is given and it's an ordinary task, `--end` is considered to be the time the task was marked completed (which is "now") and `--start` can be calculated.
* If only start is given, the duration of the event/task is used to find `--spent`, and from there `--end` can be calculated.
* If no time parameters are given, and it's an event, use dtstart and due/dtend
* If no time parameters are given, and it's a task, set completed (and `--end`) to "now", consider the duration estimate as correct, and find `--start` from there.
* The new journal dtstart date should be set to the date of the `--start` timestamp
* For a pinned task having a child event without extra participants, we consider the event data as unimportant to keep.  If the time parameters doesn't match the event dtstart/duration/dtend, then the event should simply be edited and saved back, and used as the parent for the new journal entry.
* For an ordinary event, if `--start` and `--end` doesn't match the dtstart and dtend, duplicate the event, prepend the summary with "Completed:" and let the new event be a parent of the new journal entry.
* For an ordinary task, if the duration matches, the journal entry will be a direct child of the task
* We don't want to edit the duration of a task - that's the original estimate and we may want to keep that information.  If it's an ordinary task and the duration of the task does not match, then the task information should be duplicated in a new child event, this child event should be the parent of the journal entry, and the summary should be prepended with "Completed: "

...clear as mud? :-)

## Scheduling

TODO

## Interactivity

Quite much can be gained by using any kind of desktop calendar application, mobile calendar app or caldav webui towards the calendar - though as per the cruft in the examples/task-management-examples it could probably be an idea to create some kind of a simple text UI allowing to interactively going through a list of tasks and do things on them, like:

* Setting one or more categories on all tasks missing a category
* Setting due-date and priority on all tasks missing that
* Go through all overdue and neardue tasks and mark the completed ones as completed
* Go through all events that has just passed and mark up if one really attended or not, and time spent while doing so.
* Easily go through a list of tasks suggested to be postponed and interactively select/unselect tasks from there.

In examples/task-management-examples I simply used the `list`-command combined with `--todo-template` to create new calendar-cli commands, those were sent to an editor for manual editing.  The script looks horrible, but it kind of works.
