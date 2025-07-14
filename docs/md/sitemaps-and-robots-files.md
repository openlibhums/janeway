## Sitemaps and robots files

Janeway can auto-generate sitemaps and robots files for press, journal, and repository websites.

## Sitemaps

Janeway sitemaps follow the XML-based standard specified by sitemaps.org.

They are also navigable by end users as an alternative means of navigation. An XSL style sheet is provided that implements an accessible HTML tree with named links and labelled page regions. Each website should have a link to its sitemap in the footer, so that users can discover it.

You can generate sitemaps for your Janeway sites by running the following management command:

```sh
python3 src/manage.py generate_sitemaps
```

Running this command will generate sitemaps in `src/files/sitemaps/` with the following hierarchy:

- A top-level sitemap for the press
    - Journal sitemaps for each journal
        - Issue-level sitemaps with links to articles
    - Repository sitemaps for each repository
        - Subject-level sitemaps with links to publications

Below is an example for a press that has a journal with a code of `orbit` and an issue with a primary key of 50, and a repository with short name of `olh` and a subject with a primary key of 1.

```
files/
  sitemaps/
    sitemap.xml
    orbit/
      sitemap.xml
      50_sitemap.xml
    olh/
      sitemap.xml
      1_sitemap.xml
```

Janeway has built-in views that can handle the serving of the sitemap files, which is especially useful in domain mode, since the paths can be complex to form.

## Robots

<!-- TODO -->

## Custom views or paths

If you wish, you can configure your web server to serve sitemap and robots files, rather than depend on Janeway’s sitemap views.

If you don't want to serve any sitemap or robots files, you can configure your web server to handle the URL routes that Janeway would otherwise respond to.

## Re-generating files regularly

Generation of sitemap and robots files needs to be regular to ensure they are up to date. We recommend you regenerate files every 30 minutes.

Janeway's `install_cron` command will install a cron job for you if you're using crontab. If you are not using crontab, you will need to schedule sitemap generation in some other way.
