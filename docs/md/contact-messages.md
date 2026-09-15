# Contact messages

Janeway provides a public contact form for journal and press sites. Contact people can be set for each.

## Data model

Contact messages are stored via `LogEntry` objects with `types="Contact Message"`. The `target`, which would otherwise be something like an article for workflow log entries, is the journal or press site that the contact message was submitted to.

## Recipient access to contact messages

The primary way users get contact messages is directly as emails to their inbox outside of Janeway.

However, they can also access **Contact Messages** via the manager. This view only shows the user messages sent to them, including at the staff level. This may be counter-intuitive in comparison with similar views, because most of the time, an object belonging to journal (like an article, or a task) is viewable by all editors. However, this behavior is needed for privacy, because many users will expect their message to be private to the person they select on the form. At the staff level, staff members cannot see contact messages sent to journal editors, for similar reasons.

## What happens on deletion

When a `ContactPerson` is removed, the contact messages sent to that person should still be viewable, because they are recorded as `LogEntry` objects, where the recipient’s email is saved independently of the `ContactPerson` or `Account`. The message will still appear on **Contact Messages**.

When an `Account` is removed, the `ContactPerson` is also deleted, but again, the contact messages should still exist.
