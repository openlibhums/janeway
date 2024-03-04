Robots and Sitemaps
===================

In version 1.4.1 of Janeway we are introducing the generation of Robot and Sitemap files.

Sites
-----
This document uses the word "sites" to describe the Press site, Journal site(s) and Repository site(s).

Robots
------
You can generate a robots.txt file for your Janeway sites by running the following management command:

``python3 src/manage.py generate_robots``

Running this command will generate robots.txt files. If you are using path mode it will generate a single robots file for your entire site. If you are running in domain mode it will create a top level robots.txt for sites without a domain and also an individual robots file for each site with a domain. These files are stored in `src/files/robots/`.

Here is an example directory where we are running in domain mode:

- files/
    - robots/
        - journal_orbit_robots.txt
        - repo_olh_robots.txt
        - robots.txt

The build in robots view will return the correct file automatically. At this point we recommend you leave serving the robots file to Janeway, though you could configure your webserver to serve it for you.

Sitemaps
--------
You can generate sitemap.xml files for your Janeway sites by running the following management command:

``python3 src/manage.py generate_sitemaps``

Running this command will generate:

- A top level sitemap linking to:
    - Journal sitemap linking to:
        - Issue level sitemap with links to articles
    - Repository sitemap linking to:
        - Subject level sitemap with links to publications

These files are stored in `src/files/sitemaps/` and the directory structure looks as follows:

- files/
    - sitemaps/
        - sitemap.xml
        - orbit/ - Journal
            - 50_sitemap.xml - Issue
        - olh/ - Repository
            - sitemap.xml - Root sitemap, this repository is in domain mode
            - 1_sitemap.xml - Subject



Janeway has a built in view that can handle the serving of the sitemaps files but you can also configure your webserver to serve these files for you, this can be quite complex when in domain mode and may best be left to Janeway to handle however.

Custom Robots/Sitemaps
----------------------
If you don't want Janeway to serve robots or sitemap files you can configure your webserver to handle the URL routes that Janeway uses.

Cron
----
Generation of sitemap files needs to be regular to ensure they are up to date. Janeway's ``install_cron`` command has been updated to install this command for you if you're using crontab. However you will need to schedule this manually otherwise, currently we recommend you regenerate files every 30 minutes.
