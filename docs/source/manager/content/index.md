Content
=======
The content section allows us to control the navigation menu, content pages, news and editorial team in Janeway.

The nav controller and CMS system will be overhauled as part of 1.4.

Content
-------
The Content Manager is Janeway's CMS. Pages can be created an edited using our rich text editor.

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

Navigation
----------
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
