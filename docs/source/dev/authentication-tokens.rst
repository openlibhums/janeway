Authentication
==============

Tokens
------

There are currently four different mechanisms
for retrieving tokens or codes while a user is registering, resetting
a password, or logging in via a third-party (e.g. ORCID).

* `core.models.Account.activation_code`

   This is deprecated.

* `core.models.Account.confirmation_code`

   This is used during account activation.

* `core.models.Account.OrcidToken`

   This is used during ORCID authentication.

* `core.models.Account.PasswordResetToken`

   This is used during password resets.
