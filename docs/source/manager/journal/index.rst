Journal Settings
================
.. _journal_settings:

The basic management of your journal is split into three different management interfaces.

- Journal Home Settings
- Journal Settings
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

- Journal attributes (name, ISSN, description etc)
- Force HTTPS
- Publisher information
- Control Slack logging (you can also use Discord by adding /slack onto the end of a Discord Webhook)
- Images (header, default cover, favicon etc)
- Remote settings (if this journal is hosted externally you can add its details)
- Article page settings

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