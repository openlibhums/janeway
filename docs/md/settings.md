# Settings

Janeway has various places to store settings for journals, repositories, and the press.

## Journal settings

Journal settings hold a wide variety of configuration details for each journal, and by extension each website in an installation (including the press site).

The default journal setting values live in a JSON file which is imported to the database during installation. Thereafter, staff members and editors can change the setting values for each journal via the manager and a number of other places.

## Press settings

Some default journal settings are de-facto site-level settings, including the press site (and repository sites by extension), because getting a setting value with no journal parameter returns the default. Examples include:

* `replyto_address`
* `new_user_registration`
* `user_email_change`

When there is no journal object for a site or view, Janeway logic usually concludes that things are happening at the press site level, or sometimes the repository level for repository views. Accordingly, care should be taken to keep clear whether something is a journal default or a press setting, in cases where the distinction matters.

It is worth noting that there *is* a separate `PressSetting` object, and there is a json file `press_settings.json` that at one time was loaded by a management command. However, this file is no longer typically loaded, and `PressSetting` is only used by a handful of functions, in the identifiers app. As a result, press settings that do not need to double as journal defaults are typically added as fields on the `Press` object.

## Repository settings

Repository settings are fields on the `Repository` object, and there is also a JSON file (`repository_settings.json`) which can be used to populate the fields with a management command.

## Naming guidelines

Boolean settings should be named after the thing that is turned on, without extra words like “Enable”, “Disable”, “Prevent”, or “Allow”, as long as it is clear what is meant. For example, the journal setting for including job titles in author affiliations is “Author Job Title”, not “Enable Author Job Title” or “Disable Author Job Title”.
