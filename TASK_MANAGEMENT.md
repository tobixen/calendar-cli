Managing tasks through calendar-cli
===================================

While the RFC does draw some lines on what fields are admissable in the todo-entries in the calendar, it doesn't really give good guidelines on how to use the different fields.

As of 2015-04, this document is just a collection of random thoughts on how to organize task lists.  I haven't done much research in how different software packages handles tasks, nor do I have much experience with managing task lists.  Also, calendar-cli is not really ready yet.

Calendar
--------

When should you make another calendar/task list and when does it make sense to keep things in the same calendar?

As you can give access rights to other people for a whole caldav calendar (or "task list"), it makes sense to use the calendar level to control access rights.  You would typically like to have one calendar where your family can view/add tasks, other for work, perhaps separate calendars for separate projects at work if different projects involves different people, etc.

Location
--------

A named location.

Some tasks are only possible to do at a specific location.  When being at that location, one would like to list out the pending tasks that applies for that location.

Examples:

* As a boat owner, there is always lots of maintenance and improvements work to be done on the boat.  "on the boat" is probably a good location.
* Other work can be done from home or from the office, some work should be done in the garden, etc.

Would it make sense to have a separate calendar for the boat?  If you'd like to share the task list with your family, then I think it can be in the same calendar as other family stuff.

Geo
---

A geo is a location given by coordinates.  It makes great sense to use geo ...

* if you want to stick the tasks to a map.  Probably very useful if your tasks have to be done on lots of different locations (i.e. if you are a travelling salesman or a plumber).
* if you want to set up the phone to automatically remind you about tasks i.e. when you are close to the supermarked, etc. 

Categories
----------

I'd like to think of categories as tags that can be stuck to tasks.  I.e., some tasks should be done while sitting by the keyboard.  Some tasks are related to a particular project.  Some tasks are best done when the weather is good.  Some tasks has to be done in the day time, others in the evening.  Now, add tags, so that whenever you have the chance to do some task in good weather during the daytime, you can filter out those tasks.

When to use location or geo, and when to use category?  I think that for the super market example, geo is not really fitting because it can only be one geo coordinate related to a vtodo, but there are many super markeds that can be visited.  One could also think that "supermarked" is not a good location for the same reason.

Pending-Dependent
-----------------

If one task A cannot be done without task B being done first, we say that A depends on B.  It may make sense to hide A from todolists, or maybe fade it away.  It may also make sense to push the due date for B such that there is a chance to get A done before it's due time.

The VTODO-standard does not support this kind of relationship, but it's possible to use parent-child.  The parent will then be the dependent, and the child will be the pending.

Parent-child relationship
-------------------------

This is not supported by calendar-cli as of today - but one can make a hierarchical task list.  It makes a lot of sense when having a big task that can be split up in subtasks.  Say, the task may be "build a bicycle shed".  That does take quite some planning, purchases and work, so one will definitively want to break it up in subtasks.  Ordering such a thing by categories is probably not so productive.

What about the shopping list?  "Buy squash" seems to be a subtask of "buy vegetables" which again may be a subtask of "go shopping at the supermarket" - but I think it makes more sense to use categories for that purpose.  There are two differences between the supermarket shopping and the bicycle shed ...

* Building the bicycle shed serves a purpose for it's own sake.  You're going to buy planks for building the shed, you're not building a shed to buy planks.

* "Go to the shop" is not a task for it's own sake - you'd probably not first consider "I need to go to the shop, let's add that to the task list" and then later "According to my task list, I need to go to the shop.  Let's try to make a list of what I need there".  It's more likely that you discover you're running out of sugar and then decide to add "buy sugar" to the shopping list - and you'll go to the shop because you need to buy sugar, you're not buying sugar because you need to go to the shop.

* Multiple parents may not be that trivial - you may have many different projects that requires you to buy planks.

Recurring tasks
---------------

The standard allows for recurring tasks, but doesn't really flesh out what it means that a task is recurring - except that it should show up on date searches if any of the recurrances are within the date search range.

There are two kind of recurrances - should it be done some fixed period after previous time it was done, or should it be done at some fixed period, regardless of when it was done previous time?  Say, the floor should be cleaned weekly.  You usually do it every Monday, but one week everything is so hectic that you postpone it all until Sunday.  When should the floor be washed next time?  If you actually get paid for washing the floor and you have a contract stating that you get paid a weekly sum for washing the floor weekly, then you'd probably want to wash the floor again on Sunday, even if it has been done quite recently.  Except for that, it probably doesn't make sense at all to wash again on Sunday.  You'd probably wait a whole week and wash again next Sunday.

There can be only one status and one complete-date for a vtodo, no matter if it's recurring or not.  My idea is to let the client code (calendar-cli - or maybe even the caldav library) duplicate the vtodo, the new vtodo gets the next applicable date, the old vtodo is resolved as completed.

dtstart vs due vs duration
--------------------------

I my opinion, dtstart is the earliest time you expect to start working with the vtodo, maybe even the earliest time it's possible to start.  One may want to postpone dtstart frequently.

due is the time/date when the task has to be completed, come hell or high water.  It should (in most cases) not be postponed.

Different task list implementations may behave differently, most of them is probably only concerned with the due date.

According to the RFC, either due or duration should be given, never both of them.  A dtstart and a duration should be considered as equivalent with a dtstart and a due date (where due = dtstart + duration).  I find that a bit sad, I'd like to use dtstart as the time I expect to start working with a task, duration as the time I expect to actually use on the task, and due as the date when the task really should be completed.

