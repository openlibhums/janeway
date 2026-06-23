# Task and email logs

Janeway creates a number of logs (`utils.LogEntry`) for actions that happen during the workflow. Many these actions trigger an email to be sent. The logging is thus managed by the email sending process. A log is created created that records the type of action taken in Janeway as well as details of the email.

## The notification system

The notification system, where emails and logs are created, lives in `src/utils`, and uses hooks to provide plugin functionality:

```
src/utils/notify.py
src/utils/notify_helpers.py
src/utils/notify_plugins/notify_email.py
src/utils/notify_plugins/email_log.py
src/utils/notify_plugins/notify_slack.py
```

<!--
TODO
  * Document how the notify plugins work, exactly
  * Document when to use functions like send_email_with_body_from_user, etc.

-->

## Exceptions to action logging

There are exceptions to logging that are worth noting:

- Contact messages are not logged. Instead they are simply stored as objects.
