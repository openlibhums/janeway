Issues
======
Articles do not have to be part of an issue. There are some services that do require an article have an issue or volume (such as Crossref) so we recommend that if you do continues publication that you create a yearly volume/issue to add papers to.
Articles are added to Issues during the Pre Publication stage, however, Issues can be managed on their own through the Issue Manager, a link to which is available on the Manager page and the main sidebar.

.. figure:: ../nstatic/issue_management.png

    The Issue Management page.

.. tip::
    To set the current issue, click the Make Current button. The Issue without this button _is_ the current issue.

.. tip::
    To re-order the issues you can drag and drop the rows of the tables or use the sort buttons at the top of the page.

Issue Types
-----------
Janeway comes with two issue types built in: Issue and Collection. Collections differ in so much as they are not a primary Issue for a paper but tend to be collections of papers with similar topics across multiple different issues. So an article may be in the Thomas Pynchon Collection but it's primary Issue may be Volume 1 Issue 2 2019. You can also define your own issue types in the Django admin area.

Display Settings
----------------
In the top right of the Issue Management page there is the Edit Display Settings button. This allows you to configure how issue titles are displayed.

- Volume
- Issue Number
- Year
- Custom Title

These will display in the front end in this order eg. `Volume 1 Issue 1 2019 - A Custom Issue Title`.

If you disable issue number display it will display as: Volume 1 2019 - A Custom Issue Title.

.. tip::
    If you want to display a totally custom issue title disable volume, sssue number and year and then insert whatever format you'd like the titles to be into the title field of the issue.

Creating and Editing Issue Details
----------------------------------
You can create new issues from this page using the Create Issue button and you view and edit the detail of individual issues by selecting them.

.. figure:: ../nstatic/create_issue.png

    An empty create issue form

Information on the sizes of the cover image and large image can be found in the :ref:`Styling<imageguidelines>` section

Manage an Issue
---------------
Clicking on View takes you through to the manage issue page where you can alter an individual issue. The page is split into 4 sections.

- Issue Management
- Table of Contents
- Guest Editors
- Galleys

Issue Management
^^^^^^^^^^^^^^^^
Here you can see the metadata for your issue, edit it, delete it and if the issue is published there is a link to view it on the front end.

Table of Contents
^^^^^^^^^^^^^^^^^
In the Table of contents section you can add articles to the issue, sort the sections and sort the articles within their sections.

For each section there are arrow icons that allow you to move the section up and down, each of the articles can be dragged and dropped into order from inside their section.


.. figure:: ../nstatic/issue_table_of_contents.png

    Issue table of contents