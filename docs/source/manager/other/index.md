Other
=====
The *other* section covers three things:

- Cache
- Reminders
- Email Templates

Clearing the Cache
------------------
Janeway uses a cache to speed up page loading, you can reset the cache from the Manager page by clicking the Clear Cache button.

Scheduled Reminders
-------------------
Janeway lets you define your own email reminders for overdue Reviews and Revision assignments. They are defined using the following:

- Type
    - Review or Revision reminder.
- Run Type
    - Whether to run before or after the request is due.
- Days
    - The number of days before or after the request is due this reminder should be sent.
- Template Name
    - The name of the template that should be used when sending the reminder. If this template does no exist you will be asked to create it.
- Subject
    - The email subject to send with the reminder.
    
A reminder email has access to two objects in the template:

- object - either a reviewassignment or revision object
- journal - the journal sending the reminder

You can use these objects to add context to the email. eg. {{ object.article.title }} and {{ object.reviewer.fullname }}

Email Templates
---------------
The email templates system allows you to search through and edit all of the email templates for a given journal. It is recommended you only make limited changes as these templates include placeholders for information extracted from the database.