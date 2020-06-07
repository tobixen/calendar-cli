Managing tasks through calendar-cli
===================================

While the RFC does draw some lines on what fields are admissable in the todo-entries in the calendar, it doesn't really give good guidelines on how to use the different fields.  One often gets into dilemmas ... when to use the category field vs when to use the location field vs when to branch out a completely distinct calendar, etc.  This document was originally written for myself, trying to make my own task management consistent and efficient.

I haven't done much research in how different software packages handles tasks, but I've been using calendar-cli for some task management, the document has been updated with my experiences.

Calendar scope
--------------

Different categories of tasks can be put into different calendars (and even on different caldav servers).

I believe it's best to keep as few calendars as possible, and rather use i.e. the categories field for splitting different types of tasks.

As you can give access rights to other people for a whole caldav calendar (or "task list"), it makes sense to use the calendar level to control access rights.  You would typically like to have one calendar where your family can view/add tasks, other for work, perhaps separate calendars for separate projects at work if different projects involves different people, etc.

I have a boat, and it requires a lot of maintenance and attention.  Should I create a separate calendar for boat maintenance tasks?  Considering the thoughts above, what matters is whomelse should have the rights to view and add tasks.  If the boat is a family project, use the same calendar as for other family/home-related todo-tasks.

Location
--------

A named location.  TLDR: I've ended up almost never using the location field for tasks.

With events, the location field is frequently used for which meeting room the meeting should be at, or the address of an appointment.  It's often checked up just before the meeting, or copied to the navigator when one is heading for the appointment.  Tasks are different, if you are at some specific location you would typically like to check up all tasks at that location or in the neighbourhood and see if you can do some of them.

I had an idea that some tasks are only possible to do at a specific location (i.e. as a boat owner, there are lots of tasks that can only be done "at the boat", some work can be done from home, some work has to be done from the office, some work should be done in the garden, etc), and when being at that location, one would like to list out the pending tasks that applies for that location.  However, practical experience shows that "boat", "office", "home", "garden", "grocery store", "hardware store", etc are better suited as a category than as a location.  Generally, if you have a lot of tasks connected to the same address, probably it's better to do it as a category rather than location.  If the location is a single-off thing used only for that specific task (or, perhaps, some very few tasks) then obviously it's better to use location than category.

Geo
---

A geo is a location given by coordinates.  It probably makes great sense to use geo ...

* if you want to stick the tasks to a map.  Probably very useful if your tasks have to be done on lots of different locations (i.e. if you are a travelling salesman or a plumber).
* if you want to set up the phone to automatically remind you about tasks i.e. when you are close to the supermarked, etc.  (however, most of us probably have several supermarkets we can go to, so geo doesn't make sense for that)

Practical experience: I haven't used the geo field myself.

Categories
----------

I'd like to think of categories as tags that can be stuck to tasks, and then used to filter out relevant tasks.  Some tasks should be done while sitting by the keyboard.  Some tasks are related to a particular project.  Some tasks are best done when the weather is good.  Some tasks (i.e. visit some office) has to be done in the "business day time".  Add tags for this and other relevant stuff.  When the sun is shining and you want to do some outdoor tasks, filter out the tasks with categories "sunny" or "garden".

When to use location or geo, and when to use category?  I think that for the super market example, geo is not really fitting because it can only be one geo coordinate related to a vtodo, but there are many super markeds that can be visited.  One could also think that "supermarked" is not a good location for the same reason.  In practice, I've never used location and geo, always been sticking such information into the categories instead.

While the categories field is a freetext field, it's important that the same categories are used consistently.  I made it possible to do "calendar-cli todo list --list-categories" to just take out a list of used categories.

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

Based on my interpretation of the standards, I've implemented logic in calendar-cli task completion code to duplicate the vtodo entry if it has an rrule; one vtodo ends up as completed, the other gets a new timestamp based on the rrule ("next after today".  An rrule may be set up both with fixed-time (as in "every Monday, at 10:00") and with specified intervals ("weekly"), so if you complete the task sunday evening, it will be due again Monday if it's a fixed-time rule and Sunday evening if it's with specified intervals).  The two rrules are linked togheter through the recurrance-id attribute. (perhaps this logic should be moved from calendar-cli to the caldav library).

There is no support for rrules outside the task completion code, so as for now the rrule has to be put in through another caldav client tool, through the --pdb option or through manually editing ical code.  I believe recurring tasks is an important functionality, so I will implement better support for this at some point.

dtstart vs due vs duration vs priority
--------------------------------------

I my opinion, dtstart is the earliest time you expect to start working with the vtodo, or maybe the earliest time it's possible to start.  Passing the dtstart doesn't mean you need to drop everything else and start working on the task immediately.  You'd want to postpone the dtstart just to unclutter the todo-list.

Due is the time/date when the task has to be completed, come hell or high water.  It should probably not be postponed.  Due dates should probably be set very far in the future if no specific due date is set.  You really don't want the list of tasks that are soon due or even overdue to be cluttered up with stuff that can be procrastinated even further.

Different task list implementations may behave differently, most of them is probably only concerned with the due date.

According to the RFC, either due or duration should be given, never both of them.  A dtstart and a duration should be considered as equivalent with a dtstart and a due date (where due = dtstart + duration).  I find that a bit sad, I'd like to use dtstart as the time I expect to start working with a task, duration as the time I expect to actually use on the task, and due as the date when the task really should be completed.  Calendar-cli does not support the duration field as of today.

Sometimes one gets overwhelmed, maybe one gets a week or two behind the schedule due to external circumstances.  calendar-cli supports operations like "add one week to all tasks that haven't been done yet".  As of 2015 the default due date was one week in the future.  It has been changed to one year in the future.  Probably the best practice is to keep the due date unset unless the task has a hard due date.

It's also possible to set a priority field.

The default sorting is:

* overdue tasks at the very top.
* tasks that have passed dtstart above tasks that haven't passed dtstart
* within each group, sort by due-date
* if equal due-date, sort by dtstart
* if equal due-date and dtstart, sort by priority

My usage pattern so far:

* Skip using the priority field.
* Try to handle or postpone or delete tasks that are overdue immediately, we shouldn't have any overdue tasks (oups, this didn't work out very well, as the default due date was 7 days in the future).
* On a daily basis, go through all uncategorized tasks.  All tasks should have at least one category set.  I typically do this while sitting on the metro in the morning.
* On a daily basis, look through all tasks that have passed the dtstart timestamp.  I'm considering when/how to do those tasks and (re)consider what is most urgent.  It's important to keep this list short (or it gets unwieldy, demotivating, etc), so I procrastinate everything I know I won't get done during the next few days.  I move the dtstart  timestamp to some future date - depending on my capacity, the importance of the tasks, etc, I add either some few days, weeks, months or years to it.
* Whenever I think of something that needs to be done, I add it on the task list, immediately, from the telephone.
* I've been using the timestamps to try to prioritize the tasks.
* Whenever I'm at some specific location or doing some specific work, I'll filter the task list by category, often including tasks with future dtstart.

I believe my approach of using timestamps rather than the priority field makes some sense; by looking through the "task list for this week" on a daily basis, and adding some weeks to those I know I won't be able to do anytime soon, the task list is always being circulated, there are no tasks that really gets forgotten.

Task lists tend to always grow, at some point it's important to realize ... "Those tasks are just not important enough ... I'll probably never get done with those tasks", and simply delete them.  I'm not so good at that, my alternative approach is to set a due-date and dtstart in the far future.  I remember back in 2005, 2008 was the year I was going to get things done.  Hm, didn't happen. :-)
