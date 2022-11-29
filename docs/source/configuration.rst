Technical Configuration
=======================

This section will discuss the technical configuration of Janeway focusing on the Django settings file. 

.. note:: This section is currently a work in progress.


Django Settings
---------------
Unlike traditional Django applications Janeway has two settings files, they are generally located in `src/core/`.

- janeway_global_settings.py
- settings.py (created during the installation process)

Global Settings
---------------
The global settings file is created by the Janeway team and is managed through version control. Generally speak you should not need to change anything in this file as you can use your local `settings.py` file to override variables.

Local Settings
--------------
This file is usually created during the setup process and can be based on the provided `example_settings.py` file.

- DEBUG
  - Should be set to False in any environment where an external user can access the install.
- URL_CONFIG
  - Set to either 'domain' or 'path' dependind on whether the primary way to access sites is via individual domains for each or path based urls eg. journal.press.com or press.com/journal/.
- DATABASES
  - You can set the database connection details for the install.
- CAPTCHA_TYPE
  - Can be one of three different variables: 'simple_math', 'recaptcha' or 'hcaptcha'.
    - simple_math
      - A very simple captcha using a basic mathematical question.
    - recaptcha
      - Uses Google's reCaptcha2. Has been shown to be less effective recently but v3 is not GDPR compliant. You should complete 'RECAPTCHA_PRIVATE_KEY' and 'RECAPTCHA_PUBLIC_KEY' otherwise you will get an error.
    - hcaptcha
      - Uses hcaptcha, a new addition to Janeway. You should complete 'HCAPTCHA_SITEKEY' and 'HCAPTCHA_SECRET' otherwise you will get an error.
- LOGGING
    - Provides the configuration for Python's logger. We recommend following the steps described in the `Django documentation <https://docs.djangoproject.com/en/1.11/topics/logging/>`_ for configuration.
    - By default, Janeway will log both to the console as well as to the file located at `logs/janeway.log` and rotates the file every 50MB. For production systems, you may want to change the location and/or rotation strategy as per the Django documentation


Full-text search
----------------

Janeway provides opt-in RDBMS-backed full-text search. In order to enable full-text search and indexing, the ``ENABLE_FULL_TEXT_SEARCH`` setting must be set to ``True`` under your settings file.
When enabling full-text search, the search interface will be different, offering users the ability to select what fields to perform the search on as well as allowing for results to be ordered by relevance 
(i.e. objects will be sorted by the frequency of the term in the selected fields)
Full-text search is supported on both MySQL and Postgresql backends, however due to the different implementation existing on each backend, there are a couple of extra steps to take on each.

Configuring full-text search in Postgresql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For better search performance, it is recommended to add a full-text index to the columns Janeway will search.
We recommend using a Generalized Inverted Index (GIN) with Postgresql which will result in slower writes but faster reads when compared to the alternative GiST index.

In order to create GIN indexes, one must first install the ``btree_gin`` extension. Janeway will install this extension automatically (as well as index all relevant columns for full text search) when running the
following command:

``python src/manage.py generate_search_indexes``

Additionally, we recommend setting the following setting in your ``settings.py`` file:

``CORE_FILETEXT_MODEL = "core.PGFileText"``

The setting above will change the underlying model used to index full-text articles by storing just the index in the database
instead of the entire text. If you use the ``core.PGFileText`` model, articles will only take around 10% of the original space required to store
the entire text file (This feature is only available for ``postgresql`` users)

.. warning::
    If you intend to use the ``PGFileText`` model, you must set the ``CORE_FILETEXT_MODEL`` setting before you install Janeway and/or before you
    upgrade an installation to v1.4.2. Otherwise, the migration engine will install the regular ``core.FileText`` model instead.

Configuring full-text search in MySQL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In MySQL, Janeway uses binary search mode to find results in the database. Binary search in MySQL requires the columns object of the search to be indexed.
There is a command you can run once ``ENABLE_FULL_TEXT`` is set to True

``python src/manage.py generate_search_indexes``

The above command will generate the relevant indexes for full-text search to work within Janeway.


Theming
--------
Janeway includes three core themes by default:

- OLH (Foudation)
- material (Materialize)
- clean (Bootstrap)

A list of core themes is held in janeway_global_settings.py.

Theme Structure
~~~~~~~~~~~~~~~

Generally themes follow this structure:

- /path/to/janeway/src/themes/themename/
    - assets/
        - Contains CSS/JS/Images
    - templates/
        - Contains Django templates
    - __init__.py
    - build_assets.py
        - Should contain at least one method called build that takes no arguments, it should know how to process any SCSS and copy the resulting files into the main static folder or just pass if not required. See path/to/janeway/src/themes/OLH/build_assets.py as an example.
    - README.MD

Creating a New Theme
~~~~~~~~~~~~~~~~~~~~
You are welcome to develop your own themes and can use one of the existing themes as a template of what is required. You should follow the structure above and have full template coverage.

Creating a Sub Theme
~~~~~~~~~~~~~~~~~~~~
Creating a sub theme is much easier than creating one from scratch. A sub theme is essentially a copy of one of the existing themes but with the templates that aren't required stripped out. This is useful if say, for example, you only want to customise one or two templates as you will only need to track core changes to those files.

Once you have created your sub theme you can then set for the whole install with the INSTALLATION_BASE_THEME setting or the Journal Base Theme setting for journals that are using the sub theme (located on the Manager > Journal Settings page, this setting will appear once you set the Journal Theme to your non-core theme).

An example structure for a sub theme where we want to customise only the login page:

- /path/to/janeway/src/themes/speciallogintheme/
    - assets/
    - templates/
        - core/login.html
        - press/core/login.html
    - __init__.py
    - build_assets.py
    - README.MD
