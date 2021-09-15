Journal Settings
================
.. _journal_settings:

The basic management of your journal is split into three different management interfaces.

- Journal Home Settings
- Journal Settings
- Image Settings
- Article Display Settings
- Styling Settings
- All Settings

Journal Home Settings
---------------------
The Journal Home Settings page presents a list of features that can be activated on your home page. As of 1.3.2 the following are available:

- Carousel
- About
- Featured Articles
- News
- Current Issue
- HTML

To add a homepage element, click the green *Add* button displayed in the *Add Home Page Features* list and then you can use the *[configure]* buttons to configure it. You can reorder elements by dragging and dropping them.

Carousel 
~~~~~~~~
.. _carouselanchor:

The carousel is a rotating image that can be configured to display:

- Latest Articles
- Latest News
- A combonation of both

You can select the number of articls and the number of news items to display as well as either select the articles you want or exclude those you explicity do not want to display.

About
~~~~~
This element displays a text block using the About this Journal text. This text can be edited using the _configure_ button or from the Journal Settings page detailed below.

Featured Articles
~~~~~~~~~~~~~~~~~
The featured articles element allows you to select a series of articles to display on the homepage. The selected articles are displayed in a grid that will cascade onto a new line every three articles.

News
~~~~
The news element displays a list of the most recent news items on the home page. You can configure the number of items to display, the default is 5.

Current Issue
~~~~~~~~~~~~~
Takes whichever Issue is marked as *Current* and displays its table of contents on the home page. To learn how to select a current issue check the :ref:`issue page<currentissueanchor>` .

HTML
~~~~
The HTML element is versatile, you can put any HTML you want here for example, a twitter timeline.

Journal Settings
----------------
The journal settings page is home to various configuration settings for the journal from this page you can configure:

- Journal attributes (name, ISSN, description, theme etc)
- Force HTTPS
- Publisher information
- Control Slack logging (you can also use Discord by adding /slack onto the end of a Discord Webhook)
- Remote settings (if this journal is hosted externally you can add its details)
- Language settings

Image Settings
--------------
The image settings page is new in 1.4. Most of these settings were previously in Journal Settings. The new interface provides you with a preview of the current image and is generally more useful the before.

Images you can edit from this page include:

- Journal header image
- Default hero (large) image
- Default cover image
- Favicon
- Default thumbnail
- Press override image

.. tip::
    Journal header images should be landscape where possible. For users of the OLH theme the header image should be no taller than 100px. Default thumbnails should, where possible, be square and around 100 x 100 pixels.

Article Display Settings
------------------------
The Article Display Settings page has settings for controlling the way articles look and for deciding how metrics are displayed.

- Display Guest Editors
- Suppress How to Cite
- View PDF Option
- Disable Metrics Display
- Suppress Citation Metrics


Styling Settings
----------------
This page displays some general settings for controlling the styling of your journal.

- Full Width Nav (only used by the Material theme)
- Display Editorial Team Images
- Enable Multi Page Editorial Team (splits the editorial team into pages by Group)

All Settings
------------
The all settings page lists every under-lying setting within Janeway and allows you to edit them. The setting groups are:

- Crossref
- Email
- Email Subject
- General
- Identifiers
- Preprints
- Review

This is a fallback area for editing a setting when you can't find it in the interface or for editing settings introduced into your instance. Settings can be accessed inside templates using:

`{{ journal_settings.group_name.setting_name }}` for example: `{{ journal_settings.crosscheck.enable_crosscheck }}` 

and in code as 

`request.journal.get_setting('group_name', 'setting_name')`.

The All Settings interface has been updated in v1.4 to make it easier to use. You can now search all settings by their name, code and setting group.


.. figure:: ../../nstatic/all_settings.png

    The new All Settings page.