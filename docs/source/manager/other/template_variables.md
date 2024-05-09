Email Template Variables
========================

::: {.warning}
::: {.title}
Warning
:::

This section is a work in progress started in v1.4.3.
:::

Templates
---------

### Review Assignment

Template Code: review\_assignment

This template is sent to potential reviewers inviting them to submit a
review.

Objects in this Template\'s context:

-   article, an Article object.
-   editor, an Account object.
-   review\_assignment, a ReviewAssignment object.
-   review\_url, a reversed URL with FQDN.
-   article\_details, a string with article and review information in it
    inc. Title, due date etc.

Objects
-------

Listed here is a non-exhaustive list of the objects that you may have
access to in an email template.

KEY

-   Str is plain text.
-   Int is a number.
-   FK is Foreign Key, this means the attribute is a link to another
    object.
-   M2M is Many to Many, this means the attribute links to multiple
    other objects of the given type.
-   121 is One to One, it means these two objects are linked.
-   Bool is a Boolean value and will return True or False.
-   DateTime is a field that stores a internationalised date and time.
-   Email is a validated email address.

### Account {#Object Account}

The account object stores information about users.

-   email (Email, unique)
-   username (Str)
-   first\_name (Str)
-   middle\_name (Str)
-   last\_name (Str)
-   salutation (Str)
-   biography (Str)
-   orcid (Str)
-   institution (Str)
-   department (Str)
-   twitter (Str)
-   facebook (Str)
-   linkedin (Str)
-   website (Str)
-   interest (M2M Interest)
-   country (FK Country)
-   preferred\_timezone (Str, valid timezone)
-   is\_active (Bool)
-   is\_staff (Bool)
-   date\_joined (DateTime)

### Article {#Object Article}

The article object contains the following attributes:

-   journal (FK `Object Journal`{.interpreted-text role="ref"})
-   title (Str)
-   abstract (Str)
-   owner (FK `Object Account`{.interpreted-text role="ref"})
-   keywords (FK Keyword)
-   language (Str)
-   section (FK Section)
-   license (FK License)
-   publisher\_notes (M2M PublisherNote)
-   is\_remote (Bool)
-   remote\_url (Str)
-   authors (M2M Account)
-   correspondence\_author (FK `Object Account`{.interpreted-text
    role="ref"})
-   rights (Str)
-   article\_number (Int)

### Journal {#Object Journal}

The journal object contains the following attributes:

-   code (Str)
-   name (Str)
-   current\_issue (FK Issue)
-   carousel (121 Carousel)
-   thumbnail\_image (FK File)
-   press\_image\_override (FK File)
-   default\_cover\_image (ImageField)
-   default\_large\_image (ImageField)
-   header\_image (ImageField)
-   favicon (ImageField)
-   description (Str)
-   contact\_info (Str)
-   Keywords (Keyword)
-   is\_conference (Bool)
-   is\_archived (Bool)
-   is\_remote (Bool)
-   remote\_view\_url (URLField)
-   remote\_submit\_url (URLField)
-   hide\_from\_press (Bool)
-   sequence (Int)
-   disable\_front\_end (Bool)

### ReviewAssignment {#Object Review Assignment}

-   article (FK `Object Article`{.interpreted-text role="ref"})
-   reviewer (FK `Object Account`{.interpreted-text role="ref"})
-   editor (FK `Object Account`{.interpreted-text role="ref"})
-   form (FK ReviewForm)
-   review\_round (FK ReviewRound)
-   date\_due (DateTime)
-   date\_requested (DateTime)
-   date\_accepted (DateTime)
-   date\_complete (DateTime)
-   decision (Str)
-   visibility (Bool)
-   access\_code (Str, UUID format, though not enforced)
-   is\_complete (Bool)
-   for\_author\_consumption (Bool)
-   comments\_for\_editor (Str)
-   review\_file (FK File)
-   display\_review\_file (Bool)

Using Object Variables in Templates
-----------------------------------

If I wanted to display the due date I could use:

{{ review\_assignment.date\_due }}

If I wanted to display the title of the issue this article is projected
to be in I can use:

{{ article.projected\_issue.display\_title }}

If I wanted to display an article\'s journal\'s name I would use:

{{ article.journal.name }}
