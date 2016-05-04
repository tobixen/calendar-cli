Managing tasks through calendar-cli
===================================

While the RFC does draw some lines on what fields are admissable in the todo-entries in the calendar, it doesn't really give good guidelines on how to use the different fields.

As of 2015-04, this document is just a collection of random thoughts on how to organize task lists.  I haven't done much research in how different software packages handles tasks, nor do I have much experience with managing task lists.  Also, calendar-cli is not really ready yet.

Calendar scope
--------------

Different categories of tasks can be put into different calendars (and even different caldav servers).

I believe it's best to keep as few calendars as possible, and rather use i.e. the categories field for splitting different types of tasks.

As you can give access rights to other people for a whole caldav calendar (or "task list"), it makes sense to use the calendar level to control access rights.  You would typically like to have one calendar where your family can view/add tasks, other for work, perhaps separate calendars for separate projects at work if different projects involves different people, etc.

Location
--------

A named location.

One thought - some tasks are only possible to do at a specific location.  When being at that location, one would like to list out the pending tasks that applies for that location.

Examples:

* As a boat owner, there is always lots of maintenance and improvements work to be done on the boat.  "on the boat" is probably a good location.
* Other work can be done from home or from the office, some work should be done in the garden, etc.

Would it make sense to have a separate calendar for the boat?  If you'd like to share the task list with your family, then I think it can be in the same calendar as other family stuff.

Practical experience: This fits much better into the categories field.

Second thought - some todo-items may need to be done at a specific location.  The address can be added to the location field, so it will be visible when inspecting the event at a later stage.  (I've often had a need for this with events, but not with todo items).

Geo
---

A geo is a location given by coordinates.  It makes great sense to use geo ...

* if you want to stick the tasks to a map.  Probably very useful if your tasks have to be done on lots of different locations (i.e. if you are a travelling salesman or a plumber).
* if you want to set up the phone to automatically remind you about tasks i.e. when you are close to the supermarked, etc.

Practical experience: I haven't used the geo field myself.

Categories
----------

I'd like to think of categories as tags that can be stuck to tasks.  I.e., some tasks should be done while sitting by the keyboard.  Some tasks are related to a particular project.  Some tasks are best done when the weather is good.  Some tasks has to be done in the day time, others in the evening.  Now, add tags, so that whenever you have the chance to do some task in good weather during the daytime, you can filter out those tasks.

When to use location or geo, and when to use category?  I think that for the super market example, geo is not really fitting because it can only be one geo coordinate related to a vtodo, but there are many super markeds that can be visited.  One could also think that "supermarked" is not a good location for the same reason.  In practice, I've never used location and geo, always been sticking such information into the categories instead.

Pending-Dependent
-----------------

If task A cannot be done without task B being done first, we say that A depends on B.  It may make sense to hide A from todolists, or maybe fade it away.  It may also make sense to ensure the due date for B is before the due date for A.

The VTODO-standard does not support this kind of relationship, but it's possible to use parent-child.  The parent will then be the dependent, and the child will be the pending.  See below for practical experiences.

Parent-child relationship
-------------------------

With the parent-child relationship one can make a hierarchical task list.  It makes a lot of sense when having a big task that can be split up in subtasks.  Say, the task may be "build a bicycle shed".  That does take quite some planning, purchases and work, so one will definitively want to break it up in subtasks.  Ordering such a thing by categories is probably not so productive.  This is more or less compatible with the "Pending-Dependent"-situation above; the task "build a bicycle shed" is dependent on "buy some planks", one would need to buy planks before building the bicycle shed.

What about the shopping list?  "Buy squash" seems to be a subtask of "buy vegetables" which again may be a subtask of "go shopping at the supermarket".  From a pending-dependent-perspective it still sort of checks out; you could say that one need to "go shopping" before one can "buy squash", but atoh one cannot successfully complete the "go shopping" without buying the squash.

The causality is turned on it's head in the shopping example - the purpose of "go shopping" is to "buy squash", the purpose of "build bike shed" is not to "buy planks".

I'd first add "build a shed" on the todo-list and then try to plan and see what subtasks are needed - but wrg of the sugar, I'd start with "bake a cake", then "buy sugar" and only then I would add "go shopping" to the todo-list.  (Though, my wife would probably first add "go to the shop" and then start thinking what to buy in the shop).

Practical experience:

* I've been using "supermarket" and "hardware shopping" as categories.  This have been working out fine for me, it makes much more sense than to have "supermarket shopping" and "hardware shopping" as tasks on the list.
* I never felt a compelling need to group the shopping lists inside the calendar.  On big shopping trips it makes sense to do that, but I'd typically do it externally (i.e. one of the shops I frequently go to - Biltema - I'll make the shopping list inside their web interface, then I get it out with shelf location, information if they are out of stock, prices, etc).
* Although I haven't created any bike-sheds, I've had some "projects".  First I toss the project into the task-list, with the categories "keyboard" and "thinking".  Later I take up that task and I start creating sub-tasks.  The project then disappears from my regular overview because it has unresolved dependencies.  This has worked out reasonably well for me.

It must be said that parent-child-relationships aren't very well supported yet in calendar-cli.

Recurring tasks
---------------

The standard allows for recurring tasks, but doesn't really flesh out what it means that a task is recurring - except that it should show up on date searches if any of the recurrances are within the date search range.

There are two kind of recurrances:

* Specified intervals - say, the floor should be cleaned every week.  You usually do it every Monday, but one week everything is so hectic that you postpone it all until late Sunday evening.  It would be irrational to wash it again the next day.
* Fixed-time.  If you actually get paid for washing the floor and you have a contract stating that you get paid a weekly sum for washing the floor weekly, then you'd probably want to wash the floor again on Monday, even if it has been done just recently.

There can be only one status and one complete-date for a vtodo, no matter if it's recurring or not.

Based on my interpretation of the standards, I've implemented logic in calendar-cli task completion code to duplicate the vtodo entry if it has an rrule; one vtodo ends up as completed, the other gets a new timestamp based on the rrule ("next after today".  An rrule may be set up both with fixed-time (as in "every Monday, at 10:00") and with specified intervals ("weekly"), so if you complete the task sunday evening, it will be due again Monday if it's a fixed-time rule and Sunday evening if it's with specified intervals).  The two rrules are linked togheter through the recurrance-id attribute.

There is no support for rrules outside the task completion code, so as for now the rrule has to be put in through another caldav client tool, through the --pdb option or through manually editing ical code.  I believe recurring tasks is an important functionality, so I will implement better support for this at some point.

dtstart vs due vs duration
--------------------------

I my opinion, dtstart is the earliest time you expect to start working with the vtodo, or maybe the earliest time it's possible to start.  Passing the dtstart doesn't mean you need to drop everything else and start working on the task immediately.  You'd want to postpone the dtstart just to unclutter the todo-list.

Due is the time/date when the task has to be completed, come hell or high water.  It should probably not be postponed.  Due dates should probably be set very far in the future or not set at all.  You really don't want the list of tasks that are soon due or even overdue to be cluttered up with stuff that can be procrastinated even further.

Different task list implementations may behave differently, most of them is probably only concerned with the due date.

According to the RFC, either due or duration should be given, never both of them.  A dtstart and a duration should be considered as equivalent with a dtstart and a due date (where due = dtstart + duration).  I find that a bit sad, I'd like to use dtstart as the time I expect to start working with a task, duration as the time I expect to actually use on the task, and due as the date when the task really should be completed.

