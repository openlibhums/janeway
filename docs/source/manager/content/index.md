Content
=======
The content section allows us to control the navigation menu, content pages, news and editorial team in Janeway.

The nav controller and CMS system will be overhauled as part of 1.4.

Content
-------
The Content Manager is Janeway's CMS. Pages can be created an edited using our rich text editor.

.. figure:: ../../nstatic/content_and_navigation.png

    Content and Navigation manager

Add a New Page
~~~~~~~~~~~~~~
To add a new page to your journal select "+ Add New Page". A new page requires the following:

- Name
    - This is the name of the page for the URL bar e.g. privacy-policy or author-guidelines. This field should not have any spaces in it.
- Display Name
    - The proper name for the page that will be displayed in the navigation e.g. Privacy Policy or Author Guidelines
- Content
    - HTML content, you should avoid pasting in from a text editor like Word as it will copy random styling across that will ignore your stylesheets
    
Once a new page has been created you will find it is available at https://yoururl.com/site/name e.g. https://orbit.openlibhums.org/site/privacy

Edit a Page
~~~~~~~~~~~
From the Content page you can see a list of the pages currently on your journal. To edit one, click on its title and the edit/delete buttons will appear. Select edit to make changes.

Delete a Page
~~~~~~~~~~~~~
As above click on the title and then the edit/delete buttons will appear. Press Delete to remove the page.

Navigation
~~~~~~~~~~
As of 1.3.2 Navigation is made up of:

- Fixed nav elements that can be turned on/off
- User generated navigation entries

The future intention is that all navigation will be handled via elements.

- Fixed Nav Elements
    - Home
    - News
    - Articles
    - Issues
    - Collections
    - Editorial Team
    - Submissions
    - Contact
    - Start Submission
    - Become a Reviewer
    
To add a new Navigation element: from the Content Manager page select "Edit Nav", the following elements are presented in the form:

- Link name
    - The display name for the link
- Link
    - The actual link, either local `site/privacy` or remote `https://www.google.com`
- Is External
    - If linking outside of your janeway install, this should be checked
- Sequence
    - Used to order your nav elements, it should be a positive integer (number)
- Has sub navigation
    - If this element is the first that has a drop down, check this
- Top level nav item
    - A list of elements that have "Has sub navigation" checked, if you select and item from here your new nav element will appear under the selected drop down

News Manager
------------
The news manager allows you to create news items, assign display and take down dates and upload images to display alongside them.

News items can also displayed in the :ref:`carousel<carouselanchor>`.

To add a new news item select the *News Manager*. The interface displays exiting news items on the left and a form for adding new items on the right.

.. figure:: ../../nstatic/news_manager.png

    News Manager interface
    
The form fields include:

- Title *
    - The title of the news item
- Body *
    - The HTML body of the news item
- Start display *
    - The date to start displaying this news item
- End display
    - The date to stop displaying this news item (can be left blank to display forever)
- Sequence *
    - Use for sorting when news items are posted on the same day
- Image file
    - An image file to fit the news piece, ensure you have the rights to post it
- Tags
    - A series of tags/keywords for the piece, you can filter news items by tags

.. figure:: ../../nstatic/news_item.png

    A news item with image and tags, material theme