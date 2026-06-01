# Sitemaps

Janeway can auto-generate sitemaps for press, journal, and repository websites.

Janeway sitemaps follow the XML-based standard specified by sitemaps.org.

They are also navigable by end users as an alternative means of navigation. An XSL style sheet is provided that implements an accessible HTML tree with named links and labelled page regions. Each website should have a link to its sitemap in the footer, so that users can discover it.

You can generate sitemaps for your Janeway sites by running the following management command:

```sh
python3 src/manage.py generate_sitemaps
```

Running this command will generate sitemaps in `src/files/sitemaps/` with the hierarchy that follows.

## Hierarchy

```
Press Index (siteindex)
├── Press pages (sitemap)
├── Press news (sitemap)               ← only when active news items exist
├── Journal Index (1..n, siteindex)
│   ├── Journal pages (sitemap)
│   ├── Journal news (sitemap)         ← only when active news items exist
│   ├── Issue sitemap (1..n)           ← only non-empty regular issues
│   └── Not in any issue (sitemap)     ← only when orphan published articles exist
└── Repository Index (0..n, siteindex)
    ├── Repository pages (sitemap)
    ├── Subject sitemap (1..n)         ← only non-empty subjects
    └── Not in any subject (sitemap)   ← only when orphan published preprints exist
```

Empty sub-sitemaps are skipped: no file written, no parent entry emitted.  For example, a press which has no published news, will have no news sitemap.

Each page is only listed once. Where articles are in multiple issues, or preprints in multiple subjects, they are only listed in one sitemap.

Janeway has built-in views that can handle the serving of the sitemap files, which is especially useful in domain mode, since the paths can be complex to form.

### Journal visibility

The command writes a journal sitemap for every **`is_remote=False`** journal in the filter set. The two visibility flags are handled differently:

- **`is_remote=True`** — the journal is *not hosted in Janeway*, so it has no local pages to describe. No files are written and it is not referenced anywhere.
- **`hide_from_press=True`** — the journal still has a live, hosted site, so its sitemap **is** generated. It is simply not linked from the press index. Its siteindex is therefore a top-level sitemap: `build_journal_index_context` emits **no `<janeway:higher_sitemap>`** and instead a `<janeway:note>` ("This journal is hidden from the press, …"), which the XSLT renders as a short *Note* section in place of the "Higher-level sitemap" link. With no press reference on the page, no `[journal]`/`[press]` name-clash suffix is applied.

`is_archived` is **not** a visibility flag (it is journal metadata meaning "no longer publishing"); archived journals are still browsable and are included normally. Conferences (`is_conference=True`) are hosted Janeway sites and are listed in the press index alongside journals.

### Repository visibility

`live` controls whether a repository is **linked from the press index**, not whether its sitemap is written. A repository with published preprints always gets its sitemap files generated — even when `live=False` — it is simply not referenced by the press index. This mirrors `hide_from_press` journals: a live, hosted site whose sitemap exists but carries no higher-level link. A repository with no published preprints gets no files at all.

## Custom views or paths

If you wish, you can configure your web server to serve sitemap files, rather than depend on Janeway’s sitemap views.

If you don't want to serve any sitemap files, you can configure your web server to handle the URL routes that Janeway would otherwise respond to.


## Re-generating files regularly

Generation of sitemap files needs to be regular to ensure they are up to date. We recommend you regenerate files every 30 minutes.

Janeway's `install_cron` command will install a cron job for you if you're using crontab. If you are not using crontab, you will need to schedule sitemap generation in some other way.


## Schema validation

The tests validate sample output against the schemas. Further manual validation of real-world sitemaps may be done using xmllint:
```
# from src/files/sitemaps/
xmllint --noout --schema ../../utils/schema/sitemap.xsd.xml pages_sitemap.xml news_sitemap.xml */pages_sitemap.xml */news_sitemap.xml */*_sitemap.xml
xmllint --noout --schema ../../utils/schema/siteindex.xsd.xml sitemap.xml */sitemap.xml
```


## Footers

Every front-of-house page has a visible "Sitemap" link in the theme footer. `page_sitemap_url` resolves the most specific sitemap for the current page:

| Current page | Footer "Sitemap" link target |
|---|---|
| Article | Its canonical issue sub-sitemap (`primary_issue` if set, else the first issue); the no-issue sub-sitemap if it has no regular issue |
| Preprint | Its first-alphabetical subject sub-sitemap; the no-subject sub-sitemap if it has none |
| News item | The news sub-sitemap for its owner |
| Home page | The relevant index (press / journal / repository) |
| Any other page | The pages sub-sitemap for its owner |

The article and preprint rows pick the **same single canonical sub-sitemap** the page is listed in (see "Article routing" / "Preprint routing"), so the footer link always points to a sitemap that actually contains the page.


## Expected output matrix

A condition-by-condition breakdown of what the sitemap generator produces, intended as a checklist for manual testing and for designing automated tests.

### Disambiguation

#### Name-clash disambiguation 

Suffix `[press]` / `[journal]` / `[repository]` is added **only on pages where two different entities sharing the same name actually co-occur**:

| Page | Clash set | Suffix applied to |
|---|---|---|
| Press index | press.name + all journal names + live repo names | The press's own H1/title + any clashing journal/repo child label. |
| Journal index | journal.name vs press.name | Journal H1/title + parent (press) back-link, when they collide. |
| Repository index | repo.name vs press.name | Repo H1/title + parent (press) back-link, when they collide. |
| Pages / news / issue / subject sub-sitemaps | n/a — only one entity appears | No suffix. |

#### Content-label disambiguation (date-based)

`_disambiguate_labels_by_date` runs on news, article, preprint, and pages-sitemap entries. For labels colliding case-insensitively:

| Strategy (tried in order) | Trigger |
|---|---|
| `[YYYY]` | Year alone makes the group unique. |
| `[Mon YYYY]` | Year wasn't enough. |
| `[DD Mon YYYY]` | Month-and-year wasn't enough. |
| `[#1]`, `[#2]`, … (ascending by date) | Even date-time isn't enough, **or** at least one clashing entry has `date=None` (e.g. a canonical link clashing with a CMS page that share a label/URL). |

### Which files are written

Generated under `src/files/sitemaps/`. `<code>` is `journal.code` or `repository.short_name`.

| Path | Level | Written when |
|---|---|---|
| `sitemap.xml` | press index | A `Press` row exists (i.e. always, on any real install). |
| `pages_sitemap.xml` | press | Always — Home and Accessibility are unconditional canonicals. |
| `news_sitemap.xml` | press | `press.active_news_items.exists()`. |
| `<code>/sitemap.xml` | journal index | Journal is in the run's filter set **and** `is_remote=False` — pages canonicals (Home + Accessibility) guarantee at least one page. Hidden (`hide_from_press=True`) journals are still written, but with no higher-level link (see "Journal visibility"). |
| `<code>/pages_sitemap.xml` | journal | Same gate as journal index. |
| `<code>/news_sitemap.xml` | journal | `journal.active_news_items.exists()`. |
| `<code>/<issue_id>_sitemap.xml` | issue | `issue.issue_type.code == 'issue'` **and** `_canonical_articles_for_issue(issue).exists()` (articles whose canonical issue is this one). |
| `<code>/no_issue_sitemap.xml` | journal | `_articles_not_in_any_regular_issue(journal).exists()`. |
| `<code>/sitemap.xml` | repo index | At least one subject with published preprints **or** at least one orphan preprint. Repos with no published preprints get no files at all. `live` does **not** gate writing — a non-live repo with preprints still gets files, it just isn't linked from the press index (see "Repository visibility"). |
| `<code>/pages_sitemap.xml` | repo | Same gate as repo index. |
| `<code>/<subject_id>_sitemap.xml` | subject | `_canonical_preprints_for_subject(subject).exists()` (preprints whose canonical subject is this one). |
| `<code>/no_subject_sitemap.xml` | repo | `_preprints_without_subject(repo).exists()`. |

### Siteindexes
#### Press index — child sitemap entries

Listed in the press `sitemap.xml`. Order: pages → news → journals (sorted) → repositories (sorted).

| Child | Appears when |
|---|---|
| Pages | Always (label: `"Press Pages"`). |
| News | `press.active_news_items.exists()` (label: `"Press News"`). |
| Each journal | `hide_from_press=False && !is_remote`. |
| Each repository | `live=True`. |

#### Journal index — child sitemap entries

Order: pages → news → issues (date desc) → not-in-any-issue.

| Child | Appears when |
|---|---|
| Pages | Always (label: `"Journal Pages"`). |
| News | `journal.active_news_items.exists()` (label: `"Journal News"`). |
| Each regular issue | `issue_type.code == 'issue'` **and** `_canonical_articles_for_issue(issue).exists()`. |
| Not in any issue | `_articles_not_in_any_regular_issue(journal).exists()`. |

#### Repository index — child sitemap entries

Order: pages → subjects (alphabetical) → not-in-any-subject.

| Child | Appears when |
|---|---|
| Pages | Always (label: `"Repository Pages"`). |
| Each subject | `subject.published_preprints().exists()`. |
| Not in any subject | `_preprints_without_subject(repo).exists()`. |

### Pages sitemap — canonical link presence

Canonical links are always added before CMS pages; the merged list is deduped by URL, disambiguated by date when labels clash, and sorted case-insensitive by label.

#### Press

| Canonical | Gate |
|---|---|
| Home | Always. |
| Accessibility | Always (lastmod = mtime of `src/a11y/conformance_data.json`). |
| Journals | `publishes_journals && !disable_journals`. |
| Conferences | `publishes_conferences`. |
| News | `active_news_items.exists()`. |
| Contact | Always. |
| Log in, Register | Always. |
| Privacy Policy | `privacy_policy_url` if set to a same-site (relative) path, otherwise `/site/privacy/`. An absolute/external URL is omitted — a sitemap may only list URLs on the same host. |

#### Journal

| Canonical | Gate |
|---|---|
| Home | Always. |
| Accessibility | Always. |
| Contact | `nav_contact`. |
| Articles | `nav_articles`. |
| Issues | `nav_issues`. |
| News | `active_news_items.exists()`. `nav_news` only controls the default nav link; the `/news/` URL is always served, so it's listed whenever active news exists. |
| Submissions | `nav_sub`. |
| Start Submission | `nav_start && !disable_journal_submission` setting. |
| Become a Reviewer | `nav_review`. |
| Editorial Team | `enable_editorial_display` setting (label from `editorial_group_page_name`). |
| Keyword List | `keyword_list_page` setting. |
| Log in, Register | Always. |
| Privacy Policy | `privacy_policy_url` if set to a same-site (relative) path, otherwise `/site/privacy/`. An absolute/external URL is omitted — a sitemap may only list URLs on the same host. |

#### Repository

| Canonical | Gate |
|---|---|
| Home, Accessibility, About, List, Log in, Register | All always (no setting/`nav_*` gating). The "List" link is labelled with the repo's `object_name_plural` (e.g. "Preprints"), not the literal word "List". |

#### CMS page inclusion (Press & Journal pages sitemaps)

| CMS Page state | Included? |
|---|---|
| `is_draft=True` | No. |
| `is_draft=False`, `content` null / empty / whitespace-only / HTML wrapper with no text (`<p></p>`, `<p>&nbsp;</p>`) | No. |
| `is_draft=False`, content has visible text | Yes. URL: `{owner.site_url}/site/{name}/`; label: `display_name`; lastmod: `edited`. |
| Press CMS page on a journal pages sitemap | Never — each pages sitemap lists only its own owner's CMS pages (scoped by `content_type` + `object_id`). A press page renders on journals at request time, but is not duplicated into the journal's sitemap. |

### Routing (which sub-sitemap a publication appears within)
#### Article routing

`published` = `stage=STAGE_PUBLISHED && date_published<=now()`. "Regular" issue means `issue_type.code='issue'`; collections (and any other custom issue types) are not regular.

Each published article appears in **exactly one** issue sub-sitemap — its *canonical* regular issue — matching the preprint/subject model and sitemap.org's "each URL in one place" guidance. The canonical regular issue is `primary_issue` if that is a regular issue, otherwise the first regular issue (`issues_list` order); `primary_issue` is an optional field, so the first-issue fallback covers the common case. The footer "Sitemap" link points to this same canonical issue.

| Article state | Sub-sitemap |
|---|---|
| Published, in one regular issue | That issue's `<issue_id>_sitemap.xml`. |
| Published, in two or more regular issues | Only the canonical (`primary_issue`, else first) regular issue's sitemap. |
| Published, in a regular issue AND a collection | The canonical regular issue's sitemap. **Not** in `no_issue_sitemap.xml`. |
| Published, only in collection(s) | `no_issue_sitemap.xml`. |
| Published, in no issues at all | `no_issue_sitemap.xml`. |
| Unpublished / future-dated | Nowhere. |

Journal-index inclusion uses the same canonicalised count: an issue whose articles are all canonicalised elsewhere is omitted from the index (and not written), so no empty issue sub-sitemaps appear.

#### Preprint routing

Each preprint appears in exactly one subject sub-sitemap — whichever of its subjects sorts first alphabetically by name (`_canonical_preprints_for_subject`). This matches sitemap.org's "each URL in one place" guidance and the alphabetical-first choice the `page_sitemap_url` template tag already makes for the footer link.

| Preprint state | Sub-sitemap |
|---|---|
| Published, one subject | That subject's `<subject_id>_sitemap.xml`. |
| Published, multiple subjects | Only the alphabetically-first subject's sitemap. |
| Published, no subjects | `no_subject_sitemap.xml`. |
| Unpublished | Nowhere. |

Repository-index inclusion uses the same canonicalised count: a subject whose preprints are all canonicalised elsewhere is omitted from the index (and not written), so no empty sub-sitemaps appear.

#### News item routing

| Item state | Sub-sitemap |
|---|---|
| Active (`start_display<=now` **and** `end_display>=now` or null), `content_type=press` | Press `news_sitemap.xml`. |
| Active (**same** `start_display`/`end_display` gate), `content_type=journal` | That journal's `news_sitemap.xml`. |
| `start_display` in future | Nowhere (until the date arrives). |
| `end_display` in past | Nowhere. |

Press and journal news use the **same** `ActiveNewsItemManager` (`Press.active_news_items` / `Journal.active_news_items`), so the `start_display`/`end_display` window is applied identically; only the owning `content_type` differs. Items are ordered newest first (`-posted`).

