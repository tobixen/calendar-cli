## Some potential requirements from a good calendaring system:

* 100% of all calendar users wants the possibility to "strike out" a thing from a calendar (I heard it at the CalendarFest event, so it must be true).

* It may be useful to take meeting notes directly from a calendar application (it was also said at the CalendarFest).

* Project management and accounting systems needs information on time estimates and tracking the time spent working on a task (this is a matter of fact).  Project management and accounting systems ought to be tightly coupled with the calendar system (that's my opinion).  How much time does one expect a task to take, and how much was spent on the task?  How many of the hours spent on the tasks should be billed (and how many of those should be billed at over-time rates?).  Should the employee get paid at normal rates or overtime rates for the working hours spent?

* Recurring tasks is a very useful thing! (this is my personal opinion, also ref the [TASK_MANAGEMENT document](TASK_MANAGEMENT.md))  Some of them should be done at a fixed time, no matter when it was done previous time, i.e. "prepare gym bag for my sons gym class" should be done every Tuesday, with deadline Wednesday morning.  At the other hand, the task "clean the floor" should typically be done one week after it was done previous time.

* In my opinion (ref TASK_MANAGEMENT), it makes sense on a daily basis to take out relatively short sorted list of tasks, look through it and keep the list short by procrastinating the things that seems less urgent.  I've been using the DTSTART attribute for such procrastination, but it feels a bit wrong.

* For collaboration, it's important to check when participants have avaialble time, as well as to be able to invite participants to calendar entries, and to be able to reply to invitations in such a manner that the event both appears on the personal calendar and that the organizer gets notified on whom will participate.

## Standards as they are now:

* Tasks (VTODOs) can be "striked out", but they don't stick very well to the calendar, and it cannot be used for tracking the time spent working on a task

* VJOURNAL entries on a calendar is meant exactly for meeting notes ... probably as well as recording things like who was really participating in an event, and how much time did they spend on it?  (when checking up: not really, a journal entry cannot have a duration or an end timestamp)

* Tasks have a DTSTART and either a DUE or a DURATION; the latter two are interchangable, the standard defines that the DURATION is the difference between DTSTART and DUE.  The standard is a bit unclear on exactly what those timestamps are to be used for.  I assume the DUE is the due date where a task should be completed.  This may be a very hard due date (i.e. the task "packing the suitcase" obviously needs to be done before the plane departure).  It makes sense to let DURATION be the time estimate for the task, then DTSTART will be the latest possible start time if the task is to be completed before the DUE date.  Obviously, if one expects to spend half an hour packing the suitcase and one needs to rush out the door at 19:30, one ought to start packing the suit case long before 19:30.  This breaks with my usage up until now; I've used DTSTART as the earliest point of time I'm planning to consider to start working on the task (and sometimes this may also be a well-defined timestamp - the suitcase probably shouldn't be packed several days before departure).

* It is possible to specify that a task should be a recurring task, but there is no explicit support in the RFC of completing an occurrence.  In the existing version of calendar-cli, a new "historic" task instance is created and marked complete, while dtstart is bumped in the "open" task.  (there is an alternative interpretation of "recurring task", it could mean "let's work on project A every Tuesday after lunch, all until it's completed").

* Calendar components can be linked through the RELATED-TO-attribute.  Valid relationship types are "CHILD", "PARENT" and "SIBLING".  I suppose it is intended for direct asyclic graphs, where a calendar component preferably should have only one PARENT, and where there shouldn't be loops (my grandchild cannot possibly also be my grandparent) - and that two SIBLINGs have the same PARENT.

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

* A VTODO (A) linked up as a parent to another VTODO (B) means either that B is a subtask of A or that A depends on B.  In either case, B needs to be completed before A can be completed.

* DURATION (efficiently meaning DTSTART, when DUE is set) should be used for time estimates (this breaks with my previous usage of DTSTART for prioritizing tasks).  In the case of subtasks, DURATION in the VEVENT should only indicate the "independent" time usage (so the real time estimate for the full task is the sum of the estimate for all the subtasks).  (And this is silly, since that means the   Total duration including all children tasks should eventually be calculated and presented by the calendar application.

* PRIORITY should indicate how important it is to do the task by the indicated DUE date/timestamp.  If PRIORITY=1, then the task is extremely important AND the DUE is a hard deadline.  PRIORITY=9 may mean either that DUE is a "fanciful wish" OR that the task should simply be cancelled if it's difficult to get it done prior to the DUE date.

* The calendaring system should make it possible to sort tasks based on the ratio between duration and available time until due date, and show tasks that ought to be prioritized during the next few days.

* The calendaring system should make some simple-stupid algorithm to predict the "load", how likely one is to manage the upcoming due dates.  Some parameters can be given, i.e. that one expects to be able to spend 2 hours a day for this category of tasks during the next 30 days and that tasks with priority 7 or higher can be ignored.

* If the upcoming task list is too daunting, it should be possible to semiautomatically procrastinate (move the due) upcoming items based on their priority.

* Recurring tasks is still a potential problem ... given the idea of keeping historic data as VJOURNAL ... is it at all possible to link up a VJOURNAL as a single occurrence of a recurring task?

## New calendar-cli interface

This section has been moved to a separate document, [NEW_CLI.md](NEW_CLI.md)

