## Some potential requirements from a good calendaring system:

* 100% of all calendar users wants the possibility to "strike out" a thing from a calendar (I heard it at the CalendarFest event, so it must be true).

* It may be useful to take meeting notes directly from a calendar application (it was also said at the CalendarFest).

* Project management and accounting systems needs information on time estimates and tracking the time spent working on a task (this is a matter of fact).  Project management and accounting systems ought to be tightly coupled with the calendar system (that's my opinion).  How much time does one expect a task to take, and how much was spent on the task?  How many of the hours spent on the tasks should be billed (and how many of those should be billed at over-time rates?).  Should the employee get paid at normal rates or overtime rates for the working hours spent?

* Recurring tasks is a very useful thing! (this is my personal opinion, also ref the [TASK_MANAGEMENT document](TASK_MANAGEMENT.md))  Some of them should be done at a fixed time, no matter when it was done previous time, i.e. "prepare gym bag for my sons gym class" should be done every Tuesday, with deadline Wednesday morning.  At the other hand, the task "clean the floor" should typically be done one week after it was done previous time.

* In my opinion (ref TASK_MANAGEMENT), it makes sense on a daily basis to take out relatively short sorted list of tasks, look through it and keep the list short by procrastinating the things that seems less urgent.  I've been using the DTSTART attribute for such procrastination, but it feels a bit wrong.

* For collaboration, it's important to check when participants have avaialble time, as well as to be able to invite participants to calendar entries, and to be able to reply to invitations in such a manner that the event both appears on the personal calendar and that the organizer gets notified on whom will participate.

## Standards as they are now:

* Tasks (VTODOs) can be "striked out", but they don't stick very well to the calendar, and it cannot be used for tracking the time spent working on a task

* VJOURNAL entries on a calendar is meant exactly for meeting notes ... probably as well as recording things like who was really participating in an event, and how much time did they spend on it?

* Tasks have a DTSTART and either a DUE or a DURATION; the latter two are interchangable, the standard defines that the DURATION is the difference between DTSTART and DUE.  The standard is a bit unclear on exactly what those timestamps are to be used for.  I assume the DUE is the "hard" due date where a task should be completed.  It makes sense to let DURATION be the time estimate for the task, then DTSTART will be the latest possible start time if the task is to be completed before the DUE date.  This breaks with my usage up until now; I've used DTSTART as when I'm planning to consider to start working on the task.

* It is possible to specify that a task should be a recurring task, but there is no explicit support in the RFC of completing an occurrence.  In the existing version of calendar-cli, a new "historic" task instance is created and marked complete, while dtstart is bumped in the "open" task.  (there is an alternative interpretation of "recurring task", it could mean "let's work on project A every Tuesday after lunch, all until it's completed").

* Calendar components can be linked through the RELATED-TO-attribute.  Valid relationship types are "CHILD", "PARENT" and "SIBLING".  I suppose it is intended for direct asynclic graphs, where a calendar component preferably should have only one PARENT, and where there shouldn't be loops (my grandchild cannot possibly also be my grandparent) - and that two SIBLINGs have the same PARENT.

* RFC6638 gives a framework for inviting and replying to calendar events ("scheduling"), but few calendar servers supports it fully.

## Suggestion for work flow and use (or abuse?) of the icalendar standard:

### Time tracking

When marking a task (VTODO) as completed, also make it possible to mark up how much time was spent on it (i.e. "2 hours"), optionally when it was done (default, worked on it until just now), optionally a description of what was done.  Similarly, it should be possible to write up some meeting notes and record that one actually spent time being in a meeting.

VTODO tasks are non-ideal for holding information on time spent while doing the task.  While DTSTART and DURATION, or DTSTART with COMPLETED can be used in the VTODO for marking out how much time is actually used, this will efficiently overwrite other information stored in those attributes.  I.e., DURATION may be used for time estimate, DUE (which should always be the same as DTSTART+DURATION) may be used for indicating when the task needs to be done, this is information it may be important to keep.

If one always ensures to "stick" tasks to the calendar, time tracking can be done as if it was a VEVENT.  However, event objects are also not really designed for keeping time tracking information - there is no participant state for "participated" in the event, the nearest is "accepted".  "Accepted" means "I was planning to attend to this event", it doesn't mean "I actually participated in this event".  It could also cause extra noise if one is to actively reject a calendar event after the event happened.  And the time spent on the event may be different than planned (i.e. a meeting dragging out in time or being cut short), it doesn't always make sense to edit the DTSTART/DTEND of a meeting to indicate how much time was actually spent on the meeting.

A VJOURNAL entry is supposed to describe the past, and could be a good place to store such data.  Unfortunately VJOURNAL entries cannot have DURATION nor DTEND (and it's recommended to put a date rather than a timestamp into DTSTART).  Still, I propose the usage of a VJOURNAL entry in the calendar to indicate that something has happened (and hence that time was spent on this something).  The VJOURNAL may be marked as a child of a task or an event, it means time has been spent on the activity according to the duration on the object.  If the time actually spent deviates from the scheduled or estimated duration and if it's undesireable to edit the original object, then one can simply create a new event for tracking real time spent, and mark it up as a child of the original event or task.

Overtime and billing information is considered site-specific and outside the scope - but eventually, one can use X-style attributes.

### Striking out something from the calendar

A calendar event could be "striked-out" if it has a child VJOURNAL entry.  A task should be "striked-out" if it has a COMPLETED timestamp.

### Task management

* A VEVENT linked up as a child to a VTODO means we've (tried to) allocate some time for doing the VTODO (hence "sticking" the task to the calendar).  If the task isn't marked completed by the end of the event, the calendar system should point it out.  The user should then either reschedule, procrastinate, cancel or mark it as completed.

* A VEVENT linked up as a parent to a VTODO means the VTODO needs to be completed before the event.  Once the event has passed, the VTODO should probably be cancelled if it wasn't done yet.

* DURATION should be used for time estimates (this breaks with my previous usage of DTSTART for prioritizing tasks).  For tasks with children tasks, DURATION in the VEVENT should only indicate the "independent" time usage.  Total duration including all children tasks should eventually be calculated and presented by the calendar application.

* PRIORITY should indicate how important it is to do the task by the indicated DUE date/timestamp.  If PRIORITY=1, then the task is extremely important AND the DUE is a hard deadline.  PRIORITY=9 may mean either that DUE is a "fanciful wish" OR that the task should simply be cancelled if it's difficult to get it done prior to the DUE date.

* The calendaring system should make it possible to sort tasks based on the ratio between duration and available time until due date, and show tasks that ought to be prioritized during the next few days.

* The calendaring system should make some simple-stupid algorithm to predict the "load", how likely one is to manage the upcoming due dates.  Some parameters can be given, i.e. that one expects to be able to spend 2 hours a day for this category of tasks during the next 30 days and that tasks with priority 7 or higher can be ignored.

* If the upcoming task list is too daunting, it should be possible to semiautomatically procrastinate (move the due) upcoming items based on their priority.

* Recurring tasks is still a potential problem ... given the idea of keeping historic data as VJOURNAL ... is it at all possible to link up a VJOURNAL as a single occurrence of a recurring task?

## New calendar-cli interface

### General thoughts

* calendar-cli should be a simple command line wrapper over some python library.  Logic that may be useful for python programmers should either be split out into a new calendar library ... or perhaps pushed to the caldav-library.
* Old calendar-cli stays, for backward compatibility
* Consider new tools, less reliance on "tool subcommand subcommand subcommand ..." - at the other hand, I'm fairly happy with the todo interface for listing/editing/completing.  First options to filter/sort/limit the todo item(s), then a subcommand for what to do on those items.
* Consider using the click framework
* Should consider that we at some point may want to support tools that doesn't support caldav.  Should als oconsider that we may want to support tools that doesn't support icalendar.  For instance, issue tracking through gitlab or github.
* Perhaps a new calendar-tui for increased interactivity?

### Details

Add an event, task or journal entry:

```
cal-add-event --config-section=private_calendar --set-location="Aker Brygge marina" "new years party" 2032-12-31T20:00+5h 
cal-add-todo "Buy food for the new years party" --set-due=2032-12-30T20:00 --set-duration=1h

cal-add-journal "Captain's log" 2020-12-04 'Started from Świnoujście a bit after 03AM.  Due to miscommunication, bad planning and language problems my crew member Bartek managed to throw the whole moring rope to the sea (clearly the captains fault - I didnt explain the task "release one end of the rope, let it go into the sea and pull it in" well enough, and he did ask "are you really sure about that?" before throwing both ends of the rope to the sea).  Tail wind, between 8-16 knots relative windspeed, changed a bit between broad reach and butterfly.  While going butterfly, due to a rather big wave we had an accidental jib, bad enough that the preventer rope broke off the cleat it was attached to (but luckily no damanges to the jib).  There seems to be a minor salt water leakage by the rudder.  Passed Falsterbo around 21, moored up in the guest harbour in Skanör around 22.  Very quiet as it was way outside the season.  Didnt find any obvious choice on the payment automat for harbor fee - eventually I payed SEK 100 for "tvättstuga".  I got no access to the laundry room, so I decided that 100 SEK was an OK price for staying overnight with electricity off-season in Skanör.'
```

While the specification for journal, todo and event are fairly similar, the non-optional parameters will be different due to slightly different typical use-case scenarios:

* All three should have a summary as the mandatory first parameter.
* For making todos, that should be the only mandatory parameter (as with "calendar-cli todo add").  Not all tasks have a clear due-date.  In accordance with my task management ideas above, all tasks should eventually have a due date set, but the idea is also to be able to quickly throw things on the list, and then consider an appropriate priority and due date later.
* dtstart is (according to the rfc) optional for all three classes, but it doesn't make much sense to have an event without a start time - and a journal entry should have a date.  For events, the same timestamp format is used as in the existing calendar-cli - duration can be piggybacked in the timestamp.  Change of parameter order, with "calendar-cli calendar add" the dtstart should come before the summary.  This to make "summary first" consistent for all three calendar object resource classes.
* For journal entries (as they are intended), it doesn't make much sense to add an entry without a description, so it's the mandatory second parameter.

The todo-item added above has both due timestamp and duration set, which is against the RFC.  It will be converted to dtstart and due before it's pushed to the calendar.

To get things out from the calendar, one can use the cal-agenda command.

```
cal-agenda --config-section=private --config-section=work --agenda-days=30 --event-template="{dtstart} {summary} UID={uid}" --todo-template="{due} {summary} UID={uid}"
```

cal-agenda should first print out all events starting or ending within the next 30 days, then all tasks with dtstart or due within the next 30 days.  (in my revised "task management" above, dtstart is defined as due minus estimated work time).  The tasks should be "smart sorted", according to the algorithm given in the "Task management" section above ("based on the ratio between duration and available time until due date").  It should accept several --config-section, take out all it can find from those config sections and sort the things afterwards.  Exceptions due to unreachable caldav servers or calendars not supporting tasks etc should be caught and presented nicely.

The cal-agenda is to be considered a convenience-command, it is slightly redundant.  The output of the command should be considered to be for direct human consumption, no further processing of the output should be done.  The cal-select command is the ultimate tool for a lot of things:

```
cal-select --timespan=2021-12-01+2w list
cal-select --todo --nocategories --list
cal-select --todo --nocategories -1 edit --add-category=keyboard
cal-select --todo --due-before=2021-12-01 --categories=keyboard --smart-sort list
cal-select --todo --due-before=2021-12-01 --categories=keyboard --smart-sort -1 complete
cal-select --uid=e71a6180-45a2-11ec-9605-fa163e7cfdd5 delete
cal-select --due-before=2021-12-24T15:00 --categories=housework calculate-panic-time --work-factor=0.125
cal-select --journal --dtstart-after=2021-10-01 --dtstart-before=2021-11-01 sum_hours
```

cal-select should select objects based on some criterias and then perform some action (`list`, `edit`, `postpone`, `complete`, `delete`, `calculate-panic-time`, 'sum_hours' and some more - see further below) on the objects.

The technical differences between tasks, events and journal entries are small - cal-select should basically work on all three of them unless `--todo`, `--event` or `--journal` is epxlicitly given.  If the action given does not match one or more of the objects selected (say, "completing" a journal does not make sense), the script should raise an exception before doing any modifications of the calendar.  `--offset` and `--limit` may be used to specify a handful of objects.  "-1" is shortform for "--limit 1", or typically "do this action with the top item at the list"

`--smart-sort` will give the above mentioned sort algorithm for tasks, and regular sorting by dtstart for events and journals.

The `calculate-panic-time` command will take out all planned events and todo items, count the duration of those and print out a timestamp for when you need to panic.  If it shows a timestamp in the past one should either PANIC!!! or procrastinate some tasks and cancel some events.  The command takes the `--work-factor` parameter which specifies how much of the time you will be able to concentrate on the selected tasks.  For instance, an "ordinary" parent having kids to take care of, a daytime job, plus the need for sleeping every night may perhaps in average be able to spend 3 hours a day - or 12.5% of the full day - on house work.

This should cover most regular needs for putting events on a calendar and managing tasks and todo-lists.  It does not cover "pinning" tasks to a calendar nor tracking time spent on tasks.  There may also be a need for a bit more interactivity.  Sending invites and replying to invites is also not covered.

Logical "and" should be assumed between filter selectors.  I feel uncomfortable with implementing support for paranthesis and logical operators, but there could probably be a --union parameter working as a "logical or", and some syntax should be made for the individual filters (but `--limit`, `--offset` and `--sort` should be processed after the union).  Perhaps `--categories=housework+gardenwork` should fetch everything with either "housework" or "gardenwork" as category, while `--categories=housework,kitchen` should fetch all housework to be done in the kitchen.  Or maybe `--categories=housework&gardenwork` and `--categories=housework|gardenwork` is less ambiguous.  It probably needs to be thought more through.

sum_hours will sum the duration of all objects.  Journal entries cannot have duration, so for journal entries it will sum the duration of all parents to all the journals selected.  This is supposed to be equal to the total time spent working.

### Pinning tasks to calendar

The `pin` subcommand will "pin" one or more todo-items to some specific time on the calendar.  Duration will be copied.  The tasks will be serialized.  If there are conflicting events in the same calendar, the tasks will be put after the conflicting events.  No checks will be done to ensure that the tasks ends up within ordinary working hours, outside the night hours or before the due date.  Or perhaps some sanity checks should be done ... it will be a lot of cleanup-work to be done if one accidentally forgets "-1" and adds some hundreds of items to the calendar ...

```cal-select --todo --categories=housework --smart-sort --limit=3 pin '2021-12-02 16:00'

### Time tracking

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

### Scheduling

TODO

### Interactivity

Quite much can be gained by using any kind of desktop calendar application, mobile calendar app or caldav webui towards the calendar - though as per the cruft in the examples/task-management-examples it could probably be an idea to create some kind of a simple text UI allowing to interactively going through a list of tasks and do things on them, like:

* Setting one or more categories on all tasks missing a category
* Setting due-date and priority on all tasks missing that
* Go through all overdue and neardue tasks and mark the completed ones as completed
* Go through all events that has just passed and mark up if one really attended or not, and time spent while doing so.
* Easily go through a list of tasks suggested to be postponed and interactively select/unselect tasks from there.

In examples/task-management-examples I simply used the `list`-command combined with `--todo-template` to create new calendar-cli commands, those were sent to an editor for manual editing.  The script looks horrible, but it kind of works.
