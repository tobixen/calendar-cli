## Some potential requirements from a good calendaring system:

* 100% of all calendar users wants the possibility to "strike out" a thing from a calendar (I heard it at the CalendarFest event, so it must be true).

* It may be useful to take meeting notes directly from a calendar application (it was also said at the CalendarFest).

* Project management and accounting systems needs information on time estimates and tracking the time spent working on a task (this is a matter of fact).  Project management and accounting systems ought to be tightly coupled with the calendar system (that's my opinion).  How much time does one expect a task to take, and how much was spent on the task?  How many of the hours spent on the tasks should be billed (and how many of those should be billed at over-time rates?).  Should the employee get paid at normal rates or overtime rates for the working hours spent?

* Recurring tasks is a very useful thing! (this is my personal opinion, also ref the [TASK_MANAGEMENT document](TASK_MANAGEMENT.md))  Some of them should be done at a fixed time, no matter when it was done previous time, i.e. "prepare gym bag for my sons gym class" should be done every Tuesday, with deadline Wednesday morning.  At the other hand, the task "clean the floor" should typically be done one week after it was done previous time.

* In my opinion (ref TASK_MANAGEMENT), it makes sense on a daily basis to take out relatively short sorted list of tasks, look through it and keep the list short by procrastinating the things that seems less urgent.  I've been using the DTSTART attribute for such procrastination, but it feels a bit wrong.

## Standards as they are now:

* Tasks (VTODOs) can be "striked out", but they don't stick very well to the calendar, and it cannot be used for tracking the time spent working on a task

* VJOURNAL entries on a calendar is meant exactly for meeting notes ... probably as well as recording things like who was really participating in an event, and how much time did they spend on it?

* Tasks have a DTSTART and either a DUE or a DURATION; the latter two are interchangable, the standard defines that the DURATION is the difference between DTSTART and DUE.  The standard is a bit unclear on exactly what those timestamps are to be used for.  I assume the DUE is the "hard" due date where a task should be completed.  It makes sense to let DURATION be the time estimate for the task, then DTSTART will be the latest possible start time if the task is to be completed before the DUE date.  This breaks with my usage up until now; I've used DTSTART as when I'm planning to consider to start working on the task.

* Calendar components can be linked through the RELATED-TO-attribute.  Valid relationship types are "CHILD", "PARENT" and "SIBLING".  I suppose it is intended for direct asynclic graphs, where a calendar component preferably should have only one PARENT, and where there shouldn't be loops (my grandchild cannot possibly also be my grandparent) - and that two SIBLINGs have the same PARENT.

## Suggestion for work flow and use (or abuse?) of the icalendar standard:

### Time tracking

When marking a task (VTODO) as completed, also make it possible to mark up how much time was spent on it (i.e. "2 hours"), optionally when it was done (default, worked on it until just now), optionally a description of what was done.  A VJOURNAL entry is then automatically added to the calendar, marked as a child of the task.  Overtime and billing information is considered site-specific and outside the scope - eventually, one can use X-style attributes in the VJOURNAL entry for that.

Actual participation (and time usage) on an event can also 

### Striking out something from the calendar

A "striked-out" calendar item should be presented by a VJOURNAL entry, possibly linked to a VEVENT or a completed VTODO.  If the VJOURNAL entry is linked to a VTODO that is not marked as completed, it should not be marked as "striked-out" in the calendar.

Simple tasks can be "striked out" by marking them completed, ref above.

### Task management

* A VEVENT linked up as a child to a VTODO means we've (tried to) allocate some time for doing the VTODO (hence "sticking" the task to the calendar).  If the task isn't marked completed by the end of the event, the calendar system should point it out.  The user should then either reschedule, procrastinate, cancel or mark it as completed.

* A VEVENT linked up as a parent to a VTODO means the VTODO needs to be completed before the event.  Once the event has passed, the VTODO should probably be cancelled if it wasn't done yet.

* DURATION should be used for time estimates (this breaks with my previous usage of DTSTART for prioritizing tasks).  For tasks with children tasks, DURATION in the VEVENT should only indicate the "independent" time usage.  Total duration including all children tasks should eventually be calculated and presented by the calendar application.

* PRIORITY should indicate how important it is to do the task by the indicated DUE date/timestamp.  If PRIORITY=1, then the task is extremely important AND the DUE is a hard deadline.  PRIORITY=9 may mean either that DUE is a "fanciful wish" OR that the task should simply be cancelled if it's difficult to get it done prior to the DUE date.

* The calendaring system should make ite possible to sort tasks based on the ratio between duration and available time until due date, and show tasks that ought to be prioritized during the next few days.

* The calendaring system should make some simple-stupid algorithm to predict the "load", how likely one is to manage the upcoming due dates.  Some parameters can be given, i.e. that one expects to be able to spend 2 hours a day for this category of tasks during the next 30 days and that tasks with priority 7 or higher can be ignored.

* If the upcoming task list is too daunting, it should be possible to semiautomatically procrastinate (move the due) upcoming items based on their priority.
