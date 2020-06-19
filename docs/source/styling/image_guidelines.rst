Image guidelines
================
.. _imageguidelines:
    This section describes the different images that can be uploaded in Janeway to customise the look and feel of your journal,
    as well as the recommended sizes/aspec ratios for each of theme.

Header Image
-------------------
This image is displayed on the navigation bar for all three themes, normally used for the journal logo.
It can be changed through :ref:`Manager > Journal home settings > Header Image<journal_settings>`
The maximum height of the image is 90px, however the width is not limited, making it suitable for either squared or landscape logos.

.. figure:: /_static/image_guidelines/header_image_olh.png
    :alt: Example of header image: OLH theme

    Exmaple of header image: OLH theme


.. warning::
    In the material theme, the navigation buttons and the header image are rendered within the same line, comepeting for space.
    If a very wide image is combined with a large number of navigation items, the two may overlap on narrow screens.
    If your journal has a large number of navigation links (5 or more), 
    we recommend using a dropdown menu grouping similar items.


.. figure:: /_static/image_guidelines/header_image_material.png
    :alt: Example of header image: Material theme

    Exmaple of header image: Material theme


Default Cover Image
-------------------

The cover image used by default for each issue on issues page when one is not specifically provided. This images are resized
dinamically depending on various factors (number of issues, screen size, issue title length.
It can be changed through :ref:`Manager > Journal home settings > Default Cover Image<journal_settings>` 
Specific Issue cover images can be added through Manager > Issues > Edit Issue
The recommendation for this images is to be consistent and use the same aspect ratio for bot the default cover image,
as well as for any issue cover images uploaded


.. figure:: /_static/image_guidelines/cover_image_olh.png
    :alt: Example of cover image: OLH theme

    Example of cover image: OLH theme


.. tip:: 
    For the OLH theme, cover images and issue details are rendered stacked, landscape images work better for this theme.

.. figure:: /_static/image_guidelines/cover_image_material.png
    :alt: Example of cover image: material theme

    Example of cover image: material theme

.. tip:: 
    For the material theme, cover images and issue details are rendered side by side, portrait images work better for this theme.


Default Large Image
-------------------
The large image used by default on the article page
It can be changed through :ref:`Manager > Journal home settings > Default Large Image<journal_settings>`
This a banner image that with a maximum height of 260px for the material theme and 400px for the OLH theme.
Larger Images will be scaled to this height and will be cropped width-wise in order to fit the user screen size.
For this reason, very wide landscape images work best for this element.

.. figure:: /_static/image_guidelines/article_large_image.png
    :alt: Example of large image: material theme

    Example of large image: material theme


.. tip:: 
    In the material theme, the large image width maxes out at 750px on wide screens

.. tip:: 
    In the OLH theme, the large image spans across the entire width of the screen

.. tip::
    The article images can be disabled entirely from :ref:`Manager > Journal home settings > Default Large Image<journal_settings>`


Favicon
-------
This small icon serves multiple purposes on the user's browser.

From wikipedia:
    A favicon /ˈfæv.ɪˌkɒn/ (short for favorite icon), also known as a shortcut icon, website icon, tab icon, URL icon, or bookmark icon, is a file containing one or more small icons,
    associated with a particular website or web page. A web designer can create such an icon and upload it to a website (or web page) by several means, and graphical web browsers will then make use of it.
    Browsers that provide favicon support typically display a page's favicon in the browser's address bar (sometimes in the history as well) and next to the page's name in a list of bookmarks.
    Browsers that support a tabbed document interface typically show a page's favicon next to the page's title on the tab, and site-specific browsers use the favicon as a desktop icon

We recommend using an icon of up to 100x100px which should fit most use cases.



