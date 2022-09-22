Email Template Variables
========================

.. warning::
    This section is a work in progress started in v1.4.3.

Templates
---------

Review Assignment
~~~~~~~~~~~~~~~~~
Template Code: review_assignment

This template is sent to potential reviewers inviting them to submit a review.

Objects in this Template's context:

- article, an Article object.
- editor, an Account object.
- review_assignment, a ReviewAssignment object.
- review_url, a reversed URL  with FQDN.
- article_details, a string with article and review information in it inc. Title, due date etc.


Objects
-------
Listed here is a non-exhaustive list of the objects that you may have access to in an email template.

KEY

- Str is plain text.
- Int is a number.
- FK is Foreign Key, this means the attribute is a link to another object.
- M2M is Many to Many, this means the attribute links to multiple other objects of the given type.
- 121 is One to One, it means these two objects are linked.
- Bool is a Boolean value and will return True or False.
- DateTime is a field that stores a internationalised date and time.
- Email is a validated email address.

.. _Object Account:

Account
~~~~~~~
The account object stores information about users.

- email (Email, unique)
- username (Str)
- first_name (Str)
- middle_name (Str)
- last_name (Str)
- salutation (Str)
- biography (Str)
- orcid (Str)
- institution (Str)
- department (Str)
- twitter (Str)
- facebook (Str)
- linkedin (Str)
- website (Str)
- interest (M2M Interest)
- country (FK Country)
- preferred_timezone (Str, valid timezone)
- is_active (Bool)
- is_staff (Bool)
- date_joined (DateTime)

.. _Object Article:

Article
~~~~~~~
The article object contains the following attributes:

- journal (FK :ref:`Object Journal`)
- title (Str)
- abstract (Str)
- owner (FK :ref:`Object Account`)
- keywords (FK Keyword)
- language (Str)
- section (FK Section)
- license (FK License)
- publisher_notes (M2M PublisherNote)
- is_remote (Bool)
- remote_url (Str)
- authors (M2M Account)
- correspondence_author (FK :ref:`Object Account`)
- rights (Str)
- article_number (Int)

.. _Object Journal:

Journal
~~~~~~~
The journal object contains the following attributes:

- code (Str)
- name (Str)
- current_issue (FK Issue)
- carousel (121 Carousel)
- thumbnail_image (FK File)
- press_image_override (FK File)
- default_cover_image (ImageField)
- default_large_image (ImageField)
- header_image (ImageField)
- favicon (ImageField)
- description (Str)
- contact_info (Str)
- Keywords (Keyword)
- is_conference (Bool)
- is_archived (Bool)
- is_remote (Bool)
- remote_view_url (URLField)
- remote_submit_url (URLField)
- hide_from_press (Bool)
- sequence (Int)
- disable_front_end (Bool)

.. _Object Review Assignment:

ReviewAssignment
~~~~~~~~~~~~~~~~
- article (FK :ref:`Object Article`)
- reviewer (FK :ref:`Object Account`)
- editor (FK :ref:`Object Account`)
- form (FK ReviewForm)
- review_round (FK ReviewRound)
- date_due (DateTime)
- date_requested (DateTime)
- date_accepted (DateTime)
- date_complete (DateTime)
- decision (Str)
- visibility (Bool)
- access_code (Str, UUID format, though not enforced)
- is_complete (Bool)
- for_author_consumption (Bool)
- comments_for_editor (Str)
- review_file (FK File)
- display_review_file (Bool)

Using Object Variables in Templates
-----------------------------------
If I wanted to display the due date I could use:

{{ review_assignment.date_due }}

If I wanted to display the title of the issue this article is projected to be in I can use:

{{ article.projected_issue.display_title }}

If I wanted to display an article's journal's name I would use:

{{ article.journal.name }}