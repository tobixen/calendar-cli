Managing tasks through calendar-cli
===================================

While the RFC does draw some lines on what fields are admissable in the todo-entries in the calendar, it doesn't really give good guidelines on how to use the different fields.  One often gets into dilemmas ... when to use the category field vs when to use the location field vs when to branch out a completely distinct calendar, etc.  Here are my considerations.

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

I've never used the geo field.

Categories
----------

I'd like to think of categories as tags that can be stuck to tasks, and then used to filter out relevant tasks.  Some tasks should be done while sitting by the keyboard.  Some tasks are related to a particular project.  Some tasks are best done when the weather is good.  Some tasks (i.e. visit some office) has to be done in the "business day time".  Add tags for this and other relevant stuff.  When the sun is shining and you want to do some outdoor tasks, filter out the tasks with categories "sunny" or "garden".

When to use location or geo, and when to use category?  I think that for the super market example, geo is not really fitting because it can only be one geo coordinate related to a vtodo, but there are many super markeds that can be visited.  One could also think that "supermarked" is not a good location for the same reason.  In practice, I've never used location and geo, always been sticking such information into the categories instead.

While the categories field is a freetext field, it's important that the same categories are used consistently.  I made it possible to do `calendar-cli todo list --list-categories` to just take out a list of used categories.

Pending-Dependent
-----------------

If task A cannot be done without task B being done first, we say that A depends on B.  We may want to construct a bikeshed, then paint it red.  Obviously the painting depends on the construction.  It may make sense to hide the paint job from the todolists, or maybe fade it away - when checking the list of immediate tasks to be executed, "painting the bikeshed" is just noise.  It may also make sense to ensure the due date for the construction is before the due date for the painting.

The VTODO-standard does not support this kind of relationship, but it's possible to use parent-child.  Think of the parent as the dependent and the child as the pending.  See below for practical experiences.

Parent-child relationship
-------------------------

With the parent-child relationship one can make a hierarchical task list.  It makes a lot of sense when having a big task that can be split up in subtasks.  Say, the task may be "build a bicycle shed".  That does take quite some planning, purchases and work, so one will definitively want to break it up in subtasks.

A shopping list may also be considered to be a parent-child relationship.  "Buy cucumber" seems to be a subtask of "buy vegetables" which again may be a subtask of "go shopping at the supermarket".

Every parent-child relationship can also be seen as a dependency as well, but it's a bit in reverse.  One cannot build the bike shed without first buying planks.  One cannot tick the checkbox for "go shopping" if the cucumber was not bought.  (or is it the other way?  One cannot "buy cucumber" before one has started the procedure of "go shopping"?)

There is a bit of a difference between the typical pending-dependent and the typical parent-child relationship.  In a typical "parent-child"-relationship one may want to take out hierarchical lists with the parent first, or take out simple overviews where all the details (i.e. grandchildren) are hidden.  In a typical "pending-dependent"-relationship one may want to hide the dependent (parent) and emphasize on what's needed to be done first (child).

There is another relationship also ... purpose and means.  The purpose of the shopping trip is to buy cucumber - but the purpose of building the biking shed is not to buy planks  (Unless the owner of the planks shop used some clever marketing for tricking you into building the bike shed, that is).

The purpose for buying sugar could be "bake a cake".  I would then start by adding "bake a cake" to the task list, then "buy sugar", and only then I would eventually add "go shopping" to the todo-list. (That's maybe just me.  My wife would go to the shop to buy a cucumber, and then come home with everything needed for baking a cake and more).

From my practical experience, "supermarket" and "hardware shopping" can as well be categories.  So eventually when I really need that cucumber, I can check up the full list for the category "supermarket" and come home with all ingrediences needed for making a cake.  I've never felt a compelling need to group the shopping list inside the calendar.

Although I haven't created any bike-sheds, I've had some "projects".  First I toss the project into the task-list, with the categories "keyboard" and "thinking".  Later I take up that task and I start creating sub-tasks.  The project then disappears from my regular overview because it has unresolved dependencies.  This has worked out reasonably well for me.

Parent-child-relationships aren't very well supported yet in calendar-cli yet.

Recurring tasks
---------------

The standard allows for recurring tasks, but doesn't really flesh out what it means that a task is recurring - except that it should show up on date searches if any of the recurrances are within the date search range.  Date searches for future recurrances of tasks is ... quite exotic, why would anyone want to do that?

From a "user perspective", I think there are two kind of recurrences:

* Specified intervals - say, the floor should be cleaned every week.  You usually do it every Monday, but one week everything is so hectic that you postpone it all until late Sunday evening.  It would be irrational to wash it again the next day.  And if you missed the due date with more than a week - then obviously the next recurrence is not "previous week".  (Except, one may argue that the status of previous week should be set to "CANCELLED")
* Fixed-time.  If you actually get paid for washing the floor and you have a contract stating that you get paid a weekly sum for washing the floor weekly, then you'd probably want to wash the floor again on Monday, even if it has been done just recently.  Or perhaps one of the children is having swimming at school every Tuesday, so sometime during Monday (with a hard due set to Tuesday early morning) a gym bag with swimwear and a fresh towel should be prepared for the child.  Or the yearly income tax statement, should be delivered before a hard due date.

I choose to interpret a RRULE with BY*-attributes set (like BYDAY=MO) as a recurring task with "fixed" due times, while a RRULE without BY*-attributes should be considered as a "interval"-style of recurring task.

There can be only one status and one complete-date for a vtodo, no matter if it's recurring or not.

Based on my interpretation of the standards, possibly the correct way to mark once recurrence of a recurring task as complete, is to use the RECURRENCE-ID parameter and make several instances of the same UID.  However, based on my understanding of the RFC, the timestamps in a "recurrence set" is strictly defined by the RRULE and the original DTSTART.  This does probably fit well with the fixed-time recurrences (at least if one markes a missed recurrence with CANCELLED), but it does not fit particularly well with interval-based recurrences.

I tried implementing some logic like this in calendar-cli, and it was working on DAViCal.  However, it was missing tests, and I realize that it's kind of broken.  I'm now moving this logic to the caldav layer.  I'm also creating a "safe" logic which will split the completed task into a completely separate task and editing/moving DTSTART/DUE on the recurring event.  This may be the more practical solution (perhaps combined with having a common parent for all the recurring tasks).

There is no support for rrules outside the task completion code, so as for now the rrule has to be put in through another caldav client tool, through the --pdb option or through manually editing ical code.  I believe recurring tasks is an important functionality, so I will implement better support for this at some point.

dtstart vs due vs duration
--------------------------

I don't know what they were thinking of when they created the icalendar standard.

An event may have a DTSTART and a DUE ... or alternatively, a DURATION instead of DUE.  I assume the intention is that a task with DTSTART and DURATION set is equivalent with a task with the smae DTSTART set, and a DUE set equal to DTSTART plus DURATION.  This makes a lot of sense for events, but for tasks?  Not so much!

Ok, DUE is pretty straight forward - it's the time when the task should be done.  But what is DTSTART?  Say, some bureaucracy work needs to be done "this year" - DUE should obviously be set to 1st of January at 00:00.

As of 2015 my opinion was that DTSTART is the earliest time you expect to start working with the task, or maybe the earliest time it's possible to start.  Say, we plan to sit down and do bureaucraziness the 15th of December.

Passing DTSTART doesn't mean you need to drop everything else and start working on the task immediately.  My idea was to restrict the todo-list to tasks where the DTSTART was already passed ... and then one could postpone the dtstart just to unclutter the todo-list.  However, I think it is more desirable to use the DURATION field for estimations of how long time the task will take.  Now, this bureaucraziness may be estimated to three hours of work.  That means DTSTART should be set to 21:00 at New Years eve.  Now, that's just silly!  But yeah, the DTSTART has a meaning: that's the time you need to drop everything else if you didn't do the task yet.

I have some more thoughts on project management in the other document, [NEXT_LEVEL](NEXT_LEVEL.md).

Priority
--------

The RFC defines priority as a number between 0 and 10.

0 means the priority is undefined, 1-4 means the priority is "high", 5 that it's "medium high" and 6-10 means the priority is "low".

Should tasks be done in the order of their priority?  Probably not, as there is also the DUE-date to consider.  I do have some ideas on how to sort and organize tasks in the [NEXT_LEVEL](NEXT_LEVEL.md) document.  To follow the thoughts there, let priority be defined as such:

1: The DUE timestamp MUST be met, come hell or high water.
2: The DUE timestamp SHOULD be met, if we lose it the task becomes irrelevant.
3: The DUE timestamp SHOULD be met, but worst case we can probably procrastinate it, perhaps we can apply for an extended deadline.
4: The deadline SHOULD NOT be pushed too much
5: If the deadline approaches and we have higher-priority tasks that needs to be done, then this task can be procrastinated.
6: The DUE is advisory only and expected to be pushed - but it would be nice if the task gets done within reasonable time.
7-9: Low-priority task, it would be nice if the task gets done at all ... but the DUE is overly optimistic and expected to be pushed several times.

Recommendation: split ut tasks
------------------------------

Tasks that takes more than some few hours ought to be split up into several subtasks.

To increase the probability that a high-priority task is done before the DUE, it may also be smart to split it up into subtasks/dependencies with lower priority but due dates set according to when one is expecting to get done with them.