# Domains and paths

Janeway can use one domain for a press and all its journals (path mode), or it can use a separate domain for each press or journal site (domain mode).

## Path mode examples

Path mode sites are formed with the journal code, which is often the journal acronym.

| URL                               | Name                          | Site type |
| -                                 | -                             | -         |
| https://www.openlibhums.org/      | Open Library of Humanities    | Press     |
| https://www.openlibhums.org/star/ | Syntactic Theory and Research | Journal   |
| https://www.openlibhums.org/ilr/  | International Labour Review   | Journal   |

## Domain mode examples

Domain mode sites are formed by registering a separate domain for each journal.

| URL                           | Name                          | Site type |
| -                             | -                             | -         |
| https://www.openlibhums.org/  | Open Library of Humanities    | Press     |
| https://star-linguistics.org/ | Syntactic Theory and Research | Journal   |
| https://en.ilr-rit.org/       | International Labour Review   | Journal   |

<!--
## Configuration

TODO, covering:

* settings.URL_CONFIG
* Journal.domain
* DomainAlias

-->

## Path mode as fallback

When domain mode is configured, path mode still works.

This way, indexers and archives that crawl Janeway sites based on known journal codes can discover content programmatically.

Path mode also serves as a useful alternate navigation method during initial configuration of Janeway sites, and it is helpful when troubleshooting as well.

Search engines are taught the canonical URL for each site by means of Janeway’s XML sitemaps, which always use the domain if domain mode is configured.
