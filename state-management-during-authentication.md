# Authentication tokens

There are four different undocumented or silently deprecated mechanisms
for retrieving tokens or codes while a user is registering, resetting
a password, or logging in via a third-party (e.g. ORCID):

## `core.models.Account.activation_code`

This is not marked as deprecated but it is unused.

## `core.models.Account.confirmation_code`

Used during account activation.

## `core.models.Account.OrcidToken`

Used during ORCID authentication.

## `core.models.Account.PasswordResetToken`

Used during password resets. 
