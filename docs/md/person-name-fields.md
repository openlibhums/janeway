# Person name fields

Janeway has ten or so fields related to names of people. They are spread across the `Account` and `FrozenAuthor` models.

These fields are generally subjected to plain text validation to ensure no markup is injected, since they are included in some strings that are marked safe and parsed as HTML.

## Account name fields

We have three fields for first, middle, and last name. Separate fields are needed to produce citations, alphabetize consistently, and meet downstream metadata requirements from ORCID, Crossref, JATS.

We also have `salutation` and `suffix` fields.

Note these common methods for forming the full name:

* `full_name` should be used when displaying someone’s name for other users, because it just includes first name, middle name, last name, and suffix
* `salutation_name` should be used when addressing someone, since it uses the salutation and last name, or the first name and last name if there is no salutation

## Author name fields

When author records are created from a snapshot of account fields, Janeway takes four fields, excluding the salutation: first, middle, and last, and suffix.

The salutation is not automatically copied over, because we think most people would not expect their salutation to appear by their name on a piece of published writing. However, for those who do, the name prefix field can be edited.

If you want to display an author’s full name for other users, use `full_name`. This method includes the three main name fields as well as the author name prefix and suffix fields.
