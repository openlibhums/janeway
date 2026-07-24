# Robots files

Janeway can auto-generate `robots.txt` files for press, journal, and repository websites.

## Robots

<!-- TODO -->

## Custom views or paths

If you wish, you can configure your web server to serve robots files, rather than depend on Janeway's robots views.

If you don't want to serve any robots files, you can configure your web server to handle the URL routes that Janeway would otherwise respond to.

## Re-generating files regularly

Generation of robots files needs to be regular to ensure they are up to date. We recommend you regenerate files every 30 minutes.

Janeway's `install_cron` command will install a cron job for you if you're using crontab. If you are not using crontab, you will need to schedule generation in some other way.
