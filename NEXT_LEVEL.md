## Tasks vs events vs journals

In my paradigm, a task is a planned activity that should be done, but not at a specific time (but possibly it should be done within a specific time interval).  When it's done - or when it is deemed irrelevant to do it - it can be striken out from the list.  An event is something that should be done at a relatively well-defined time.  While you may come an hour early or late to the Saturday night party and still have a lot of fun - if you come at the wrong date, then there won't be a party.

It's not always black and white - events may be task-alike (like an appointment that will have to be rescheduled if you miss it) and tasks may be event-alike (i.e. with a very hard due-time and that cannot be done long time before the due date).

Both events and tasks generally contain infomration about future plans, journals contain information about the past.

## Some potential requirements from a good calendaring system:

* 100% of all calendar users wants the possibility to "strike out" a thing from a calendar (I heard it at the CalendarFest event, so it must be true - though it does break with my paradigm).

* It may be useful to take meeting notes directly from a calendar application (it was also said at the CalendarFest).

* Project management and accounting systems needs information on time estimates and tracking the time spent working on a task (this is a matter of fact).  Project management and accounting systems ought to be tightly coupled with the calendar system (that's my opinion).  How much time does one expect a task to take, and how much was spent on the task?  How many of the hours spent on the tasks should be billed (and how many of those should be billed at over-time rates?).  Should the employee get paid at normal rates or overtime rates for the working hours spent?

* Recurring tasks is a very useful thing! (this is my personal opinion, also ref the [TASK_MANAGEMENT document](TASK_MANAGEMENT.md))  Some of them should be done at a fixed time, no matter when it was done previous time, i.e. "prepare gym bag for my sons gym class" should be done every Tuesday, with deadline Wednesday morning.  At the other hand, the task "clean the floor" should typically be done one week after it was done previous time.

* In my opinion (ref TASK_MANAGEMENT), it makes sense on a daily basis to take out relatively short sorted list of tasks, look through it and keep the list short by procrastinating the things that seems less urgent.  I've been using the DTSTART attribute for such procrastination, but it feels a bit wrong.

* For collaboration, it's important to check when participants have available time, as well as to be able to invite participants to calendar entries, and to be able to reply to invitations in such a manner that the event both appears on the personal calendar and that the organizer gets notified on whom will participate.

## Standards as they are now:

The RFC specifies three different kind of calendar resource object types, it's the VJOURNAL, VTODO and VEVENT.  From a technical point of view, the differences are mostly those:

* The VEVENT has a DTEND, the VTODO has a DUE, and the VJOURNAL ... has neither.
* The VEVENT is generally expected to have a DTSTART.  The VJOURNAL is generally expected to have a DTSTART set to a date.  A VTODO need not have a DTSTART.

Calendaring systems usually have very different user interfaces for tasks and events (and journals are generally not used).  Generally, tasks can be "striked out", but they don't stick very well to the calendar.  None of the three types are well-suited for tracking the time spent working on a task or attending to a meeting.

VJOURNAL entries on a calendar is meant exactly for meeting notes ... probably as well as recording things like who was really participating in an event, unfortunately not possible to track how much time they spend on it (A journal entry cannot have a duration or an end timestamp).

Tasks may have a DTSTART and either a DUE or a DURATION; the latter two are interchangable, the standard defines that the DURATION is the difference between DTSTART and DUE.  The standard is a bit unclear on exactly what those timestamps are to be used for.  I assume the DUE is the due date where a task should be completed.  This may be a very hard due date (i.e. the task "packing the suitcase" obviously needs to be done before the plane departure).  It makes sense to let DURATION be the time estimate for the task, then DTSTART will be the latest possible start time if the task is to be completed before the DUE date.  Obviously, if one expects to spend half an hour packing the suitcase and one needs to rush out the door at 19:30, one ought to start packing the suit case long before 19:30.  This breaks with my usage up until now; I've used DTSTART as the earliest point of time I'm planning to consider to start working on the task (and sometimes this may also be a well-defined timestamp - the suitcase probably shouldn't be packed several days before departure).

* It is possible to specify that a task should be a recurring task, but there is no explicit support in the RFC of completing an occurrence.  In the existing version of calendar-cli, a new "historic" task instance is created and marked complete, while dtstart is bumped in the "open" task.  (there is an alternative interpretation of "recurring task", it could mean "let's work on project A every Tuesday after lunch, all until it's completed").

* Calendar components can be linked through the RELATED-TO-attribute.  Valid relationship types are "CHILD", "PARENT" and "SIBLING".  I suppose it is intended for direct asyclic graphs, where a calendar component preferably should have only one PARENT, and where there shouldn't be loops (my grandchild cannot possibly also be my grandparent) - and that two SIBLINGs have the same PARENT.

* RFC6638 gives a framework for inviting and replying to calendar events ("scheduling"), but few calendar servers supports it fully.

## Suggestion for work flow and use (or abuse?) of the icalendar standard:

### Sticking a task to the calendar

One may have an agenda with lots of events and some "unallocated" time in between, and one may want to try to plan getting specific tasks done at specific times.  It may be nice to get this into the calendar.

If a task has a DTSTART set, it may be interpreted as the time one actually plan to start working with the task - but it's non-ideal, for one thing most calendaring user interfaces will not "stick" the task to the calendar on that, and the DTSTART attribute may be used for other purposes.

It may make sense to make a VTOOD stick to the calendar by making up a VEVENT and letting that VEVENT be a child of the VTODO.

Similarly, for calendar items that "needs" to be "striken out" (say, some course you need to take - if you miss the scheduled course time then you need to take it at a later time), it may make sense to create a "parent task" for it.

Perhaps even make it to a general rule that all activities should be registered on the calendar as a VTODO/VEVENT parent/child pair, where the VTODO contains time estimates and the VEVENT contains planned time for doing the VTODO.

### Time tracking

When marking a task (VTODO) as completed, it ought to be possible to mark up how much time was spent on it (i.e. "2 hours"), optionally when it was done (default, worked on it until just now), optionally a description of what was done.  Similarly, for a VEVENT it should be possible to write up i.e. meeting notes and record that one actually spent time being in a meeting.

VTODO tasks are non-ideal for holding information on time spent while doing the task.  While DTSTART and DURATION, or DTSTART with COMPLETED can be used in the VTODO for marking out how much time is actually used, this will efficiently overwrite other information stored in those attributes.  I.e., DURATION may be used for time estimate, DUE may be used for indicating when the task needs to be done, this is information it may be important to keep (but to make things more difficult, DUE and DURATION are mutually exlusive).

If one always ensures to "stick" tasks to the calendar, time tracking can be done in the DTSTART/DTEND of the VEVENT.  However, event objects are also not really designed for keeping time tracking information.  As said, the primary purpose is to contain information about the future - not the past.  There is no participant state for "participated" in the event, the nearest is "accepted".  "Accepted" means "I was planning to attend to this event", it doesn't mean "I actually participated in this event".  It could also cause extra noise if one is to actively reject a calendar event after the event happened, as it may cause notifications to be sent to the organizer.  To make it even more complicated, the time spent on the event may be different than planned (i.e. a meeting dragging out in time or being cut short), it doesn't always make sense to edit the DTSTART/DTEND of a meeting to indicate how much time was actually spent on the meeting.

A VJOURNAL entry is (the only entry) supposed to describe the past, and could be a good place to store such data.  Unfortunately VJOURNAL entries cannot have DURATION nor DTEND (and it's recommended to put a date rather than a timestamp into DTSTART).

It is a great mess - the designers of the calendar standards absolutely didn't consider the need of tracking tim spent.

My proposal is to let a VJOURNAL be a child of a VEVENT to mark that the VEVENT took place and that one participated in it.  If things went as planned, it's straight forward.  If things didn't go as planned, then ... either one may need to edit the VEVENT or create a separate VEVENT (which may be a child of the original VEVENT) containing the correct timestamps.  If it was a VTODO and it wasn't "stuck" to the calendar, then it's trivial to make an after-the-fact VEVENT (just be careful that no calendar invites are sent out).

Overtime and billing information is so far considered site-specific and outside the scope.

### Striking out something from the calendar

This sort of leaves us with two ways of "striking out" something.  There is the traditional way of marking the task as COMPLETED.  Now if the task is connected to a VEVENT, the calendar item should also be striken out.

The second way is to make sure there is a VJOURNAL attached as a child of the VEVENT or a (grand)grandchild of the VTODO.

Those two ways of striking out things have fundamentally different meanings.  The first is to mark that a task is done and closed and does not need to be revisited.  The second is to mark that work time was spent on the task or event.  One would typically want to use both kind of "strikes".  Only the first one if one is to mark that no significant work time was spent on the task (i.e. because the task has been cancelled, or because the work time spent has been accounted for somewhere else), and only the second one (and then create more events/journals later) if work time was spent but the task was not completed.

### Task management

* A VEVENT linked up as a child to a VTODO means we've (tried to) allocate some time for doing the VTODO (hence "sticking" the task to the calendar).  If the task isn't marked completed by the end of the event, the calendar system should point it out.  The user should then either reschedule, procrastinate, cancel, mark it as completed, or mark it as partially done.

* A VEVENT linked up as a parent to a VTODO means the VTODO needs to be completed before the event.  Once the event has passed, the VTODO should probably be cancelled if it wasn't done yet.

* A VTODO (A) linked up as a parent to another VTODO (B) means either that B is a subtask of A or that A depends on B.  In either case, B needs to be completed before A can be completed.

* DURATION (efficiently meaning DTSTART, when DUE is set) should be used for time estimates (this breaks with my previous usage of DTSTART as the earliest time I would expect starting to work on the task).  In the case of child/parent tasks, DURATION should (probably?) only indicate the "independent" time usage - so the full estimate of the time consumption for the whole project is the sum of the duration of all the VTODOs in the project.  This may be a bit silly, as it either means the DUE for the "root task" must be set almost at project start (though, it may make sense if planning things in a top-down fashion), or that the DTSTART for the "root task" must be set almost at the project end (may make sense when considering dependencies - the subtasks needs to be done first).

* PRIORITY should indicate how important it is to do the task by the indicated DUE date/timestamp.  If PRIORITY=1, then the task is extremely important AND the DUE is a hard deadline.  PRIORITY=9 may mean either that DUE is a "fanciful wish" OR that the task should simply be cancelled if it's difficult to get it done prior to the DUE date.

* The calendaring system should make it possible to sort tasks based on the ratio between duration and available time until due date, and show tasks that ought to be prioritized during the next few days.

* The calendaring system should make some simple-stupid algorithm to predict the "load", how likely one is to manage the upcoming due dates.  Some parameters can be given, i.e. that one expects to be able to spend 2 hours a day for this category of tasks during the next 30 days and that tasks with priority 7 or higher can be ignored.

* If the upcoming task list is too daunting, it should be possible to semiautomatically procrastinate (move the due) upcoming items based on their priority.

* Recurring tasks is still a potential problem.

## New calendar-cli interface

This section has been moved to a separate document, [NEW_CLI.md](NEW_CLI.md)

