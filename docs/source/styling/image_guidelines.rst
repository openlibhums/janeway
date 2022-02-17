.. _imageguidelines:

Image guidelines
================

This section describes the different images that can be uploaded in Janeway to customise the look and feel of your journal, as well as the recommended sizes and aspect ratios for each theme.

Header Image
------------
This image is displayed on the navigation bar for all three themes and is normally used for the journal logo. It can be changed through the :ref:`settings in the journal's Manager<journal_settings>` (Manager > Journal Settings).

The maximum height of the image is 90px, but the width is not limited, making it suitable for either square or landscape logos.

.. figure:: /_static/image_guidelines/header_image_olh.png
    :alt: Example of header image with OLH theme
    :class: screenshot

    Example of header image with OLH theme


.. figure:: /_static/image_guidelines/header_image_material.png
    :alt: Example of header image with Material theme
    :class: screenshot

    Exmaple of header image with Material theme

.. warning::
    In the material theme, the navigation buttons and the header image are rendered within the same line, comepeting for space. If a very wide image is combined with a large number of navigation items, the two may overlap on narrow screens. If your journal has a large number of navigation links (5 or more), we recommend using a dropdown menu grouping similar items.


Cover Image
-----------

Cover images are used for issue covers, as displayed on the Issues page. You can set them individually, and you can set a default to be used when one is not specifically provided for an issue. Add specific issue cover images under :ref:`Issue Management<articles_issues_guidelines>`, and change the default through :ref:`Journal Settings<journal_settings>`.

These images are resized dynamically depending on various factors (number of issues, screen size, issue title length). The recommendation is to be consistent and use the same aspect ratio for both the default cover image and for any issue cover images uploaded.


.. figure:: /_static/image_guidelines/cover_image_olh.png
    :alt: Example of cover image with OLH theme
    :class: screenshot

    Example of cover image with OLH theme


.. tip:: 
    For the OLH theme, cover images and issue details are rendered stacked, so landscape images work better for this theme.

.. figure:: /_static/image_guidelines/cover_image_material.png
    :alt: Example of cover image with material theme
    :class: screenshot

    Example of cover image with material theme

.. tip:: 
    For the material theme, cover images and issue details are rendered side by side, so portrait images work better for this theme.


Large Image
-----------
Large images are used on article pages, on issue pages, and in any carousel that draws in these elements to the journal home page. You can set them individually, and you can set a default to be used in all other cases. You can set large images for articles in the Manager under :ref:`Articles and Issues<articles_issues_guidelines>`. The default can can be changed through :ref:`Journal Settings<journal_settings>`.

The large image has a maximum height of 260px for the material theme and 400px for the OLH theme. Any image larger than 750x324 pixels will be compressed to fit those dimensions, and then it will be cropped horizontally to fit the user screen size. For this reason, very wide landscape images work best for this element.

.. figure:: /_static/image_guidelines/article_large_image.png
    :alt: Example of large image: material theme
    :class: screenshot

    Example of large image: material theme


.. tip::
    In the material theme, the large image width maxes out at 750px on wide screens.

.. tip::
    In the OLH theme, the large image spans across the entire width of the screen.

.. tip::
    The article images can be disabled entirely in the Manager under :ref:`Articles and Issues<articles_issues_guidelines>`.


Favicon
-------
This small icon serves multiple purposes in the user's browser.

From wikipedia:
    A favicon /ˈfæv.ɪˌkɒn/ (short for favorite icon), also known as a shortcut icon, website icon, tab icon, URL icon, or bookmark icon, is a file containing one or more small icons, associated with a particular website or web page. A web designer can create such an icon and upload it to a website (or web page) by several means, and graphical web browsers will then make use of it. Browsers that provide favicon support typically display a page's favicon in the browser's address bar (sometimes in the history as well) and next to the page's name in a list of bookmarks. Browsers that support a tabbed document interface typically show a page's favicon next to the page's title on the tab, and site-specific browsers use the favicon as a desktop icon.

We recommend using an icon of up to 100x100px, as this should fit most use cases.
