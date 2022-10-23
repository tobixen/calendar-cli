# On the "next level" calendar-cli - a full-featured tool for calendar management, project management and time tracking

This document is dedicated to my rubber ducky - but if anyone else has the patience to read through it, feedback is appreciated.

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

### Calendar resource object types

The RFC specifies three different kind of calendar resource object types, it's the VJOURNAL, VTODO and VEVENT.  From a technical point of view, the differences are mostly in what timestamps the object holds.  The VEVENT has a DTEND, the VTODO has a DUE, and the VJOURNAL ... has neither.  The VEVENT is generally expected to have a DTSTART.  The VJOURNAL is generally expected to have a DTSTART set to a date.  A VTODO need not have a DTSTART.  There is also the STATE field that can have different values depending on the object type.  I think all other differences enforced by the RFC is minor.

Calendaring systems usually have very different user interfaces for tasks and events (and journals are generally not used).  Generally, tasks can be "striked out", but they don't stick very well to the calendar.  None of the three types are well-suited for tracking the time spent working on a task or attending to a meeting.

VJOURNAL entries on a calendar is the correct place to store meeting notes ... probably as well as recording things like who was really participating in an event.  It can also be used for recording a diary or make other notes on what one has done during the day.

VEVENT and VTODO is generally optimized for keeping information about the future - while VJOURNAL is supposed to be used for keeping information about the past.  However, the RFC is not explicit on this, and I haven't heard of any implementations that denies one creating tasks/events with timestamps in the past nor journals with DTSTART in the future.

### More on timestamps

A VJOURNAL can only contain a DTSTART, and no DURATION or DTEND.  This makes it impossible to use the VJOURNAL to track how much time has been spent.  I think this is stupid - as written above, time tracking is something we would like to do at the calendar level, and since it's information on things that has already happened, VJOURNAL is the only logic place to put it.

A VTODO may have a DTSTART and a DUE.  I think the DUE timestamp is relatively easy to define, it's the time you, your leader, your customer and/or your significant other and/or other relevant parties expects the task to be completed.  It may be a hard deadline, or it may be a "soft" target that may be pushed on later.  The DTSTART is however a bit more tricky, I can see the field being used for quite different purposes:

* The earliest possible time one can start working with a task (or the earliest possible time one expects to be able to start working with it)
* The time one is actually planning to start working with it
* The latest possible time one can start working with it, and still be done before the due time.
* The time one actually started working with the task

As an example, consider a tax report to be filled out and sent to the authorities, the latest at the end of April.  Consider that one will have to pay fines if it is not delivered before midnight the night before 1st of May.  One cannot start with it before all the data one needs is available, perhaps 1st of April is the earliest one can start.  One may plan to work with during a specific Sunday in the middle of April.  If it takes three hours to complete the report, the very latest one can start is at 21:00 night before the 1st of May, but it would be very silly to actually start at that time.  And perhaps one actually got started with it at noon at the 25th of April.

A VEVENT and a VTODO may take a DURATION, but it cannot be combined with DTEND or DUE.  While the RFC is not explicit on it, it is my understanding that DURATION and DTEND/DUE is interchangable - if DTSTART and DTEND/DUE is set, the DURATION is implicitly the difference between those two - an object with DTSTART and DURATION set is equivalent with an object with DTSTART and DTEND/DUE set.  For the rest of the document, DURATION is understood to be the difference between DTSTART and DTEND/DUE.  In my head, tasks have a DUE and a DURATION while the DTSTART is a bit more abstranct.  Hence, setting or changing the DURATION of a task may efficiently mean "setting the DTSTART" - and the definition of DTSTART depends on the definition of DURATION.  Is the DURATION the time estimate for completing the task?  Then DTSTART will have to be the very latest one can start with the task and still complete before the DUE.

Other observations:

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

It is a great mess - the designers of the calendar standards absolutely didn't consider the need of tracking time spent.

While working with code for completion of a reccurrence of a recurring tasks, I realized that we're actually storing information on *what has happened* when we're changing the status to "completed" and adding a timestamp for when it was completed.  For a recurring task we're also duplicating the information in the task.  Hence we can keep the original time information in the original recurring task but store actual time spent in the recurrence.  The time spent may *either* be stored in the DURATION or through the difference between DTSTART and COMPLETED timestamp.  To avoid any kind of confusion, I propose to set DUE and COMPLETED to the same timestamp, and let the DURATION indicate the time spent.  Non-recurring tasks may be hand-crafted into recurring tasks with COUNT set to one.  That does feel like a rather dirty workaround though.

One idea may be to always make a VJOURNAL, a child of a VEVENT or VTODO, to mark either that the VEVENT took place and that one participated in it, or that one did spend time working on a task.  For a VEVENT, if things went as planned, it's straight forward - the DURATION of said event marks the time spent on it.  If things didn't go as planned, then ... either one may need to edit the VEVENT or create a separate VEVENT (which may be a child of the original VEVENT) containing the correct timestamps.  If it was a VTODO and it wasn't "stuck" to the calendar, then it's trivial to make an after-the-fact VEVENT (just be careful that no calendar invites are sent out).  For a VTODO one may hack up something by considering the difference between the journal DTSTART and the task COMPLETION timestamp to be the actual time worked on the task.  Or it's possible to track the time by retroactively "stick the task to the calendar", and let the VJOURNAL be a child of a VEVENT which is a child of the VTODO.

So I haven't concluded yet on how it is best to do time tracking on tasks, but there are some options.  In any case, I think that consistently using a VJOURNAL entry to mark that one has actually participated in an event or spent time working on a task is a good idea.

There is additional complexity that the time spent may be flagged as overtime, and that there may be billing information as well.  I'm considering it to be site-specific and outside the scope.  It may be possible to squeeze this information in somewhere, maybe in the CATEGORIES field, or maybe in some X-NONSTANDARD attributes.

### Striking out something from the calendar

The considerations above sort of leaves us with two ways of "striking out" something.  There is the traditional way of marking the task as COMPLETED.  Now if the task is connected to a VEVENT, the calendar item should also be striken out.

The second way is to make sure there is a VJOURNAL attached as a child of the VEVENT or a (grand)grandchild of the VTODO.

Those two ways of striking out things have fundamentally different meanings - the first is to mark that a task is done and closed and does not need to be revisited, the second is to mark that work time was spent on the task or event.  This may be combined in different ways;

* If one did some work and completed a tas, one would typically want to use both kind of "strikes".
* Sometimes one may want to mark a task as "completed" or "cancelled" even if one hasn't spent time on it - maybe because it has become irrelevant or because it has already been done (by someone else, or the work has been "piggybacked" in another task, time consumption counted for in another project, etc)
* Sometimes one has spent time on a task without completing it (maybe partly completed, maybe wasted some time on it before marking it as "cancelled", etc), then one would like to create the journal entry but without marking it as complete.

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

