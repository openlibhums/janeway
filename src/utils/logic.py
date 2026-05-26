import datetime
import html
import os
import hashlib
import hmac
from urllib.parse import SplitResult, urlencode, urlparse, unquote

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import QueryDict
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from core.middleware import GlobalRequestMiddleware
from cron.models import Request
from utils import models, notify_helpers
from utils.logger import get_logger
from utils.function_cache import cache
from janeway import __version__ as janeway_version
from repository import models as repo_models
from press import models as press_models
from submission import models as submission_models
from comms import models as comms_models
from cms import models as cms_models


logger = get_logger(__name__)


def parse_mailgun_webhook(post):
    message_id = post.get("Message-Id")
    token = post.get("token")
    timestamp = post.get("timestamp")
    signature = post.get("signature")
    mailgun_event = post.get("event")

    try:
        event = models.LogEntry.objects.get(message_id=message_id)
    except models.LogEntry.DoesNotExist:
        return "No log entry with that message ID found."

    if event and (mailgun_event == "dropped" or mailgun_event == "bounced"):
        event.message_status = "failed"
        event.save()
        send_bounce_notification_to_event_actor(event)
        return "Message dropped, actor notified."
    elif event and mailgun_event == "delivered":
        event.message_status = "delivered"
        event.save()
        return "Message marked as delivered."


def verify_webhook(token, timestamp, signature):
    api_key = settings.MAILGUN_ACCESS_KEY.encode("utf-8")
    timestamp = timestamp.encode("utf-8")
    token = token.encode("utf-8")
    signature = signature.encode("utf-8")

    hmac_digest = hmac.new(
        key=api_key,
        msg="{}{}".format(timestamp, token).encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, hmac_digest.encode("utf-8"))


def send_bounce_notification_to_event_actor(event):
    """
    Attempts to send a notification email to an actor when a message bounces.
    Messages are only send to staff, editors and repository managers.
    """
    actor = event.actor
    target = event.target

    # set to the main contact, and then attempt to find a better match
    press = press_models.Press.objects.all()[0]
    to = press.main_contact

    # fake a request object
    request = Request()
    request.press = press
    request.META = {}
    request.model_content_type = None
    request.user = None

    if actor and target:
        if actor.is_staff or actor.is_superuser:
            to = actor.email

        # target could be an article or a preprint, lets find out
        if isinstance(target, submission_models.Article):
            # check if the actor is an editor for the article's journal
            if actor in target.journal.editors():
                to = actor.email
            request.site_type = target.journal
            request.journal = target.journal
        elif isinstance(target, repo_models.Preprint):
            # check if the actor is a manager for the preprint's repo
            if actor in target.repository.managers.all():
                to = actor.email
            request.site_type = target.repository
            request.repository = target.repository

    # currently this feature is set up for article and preprint emails.
    # if no site type is set, we shouldn't try to send a bounce email.
    if request.site_type:
        # Setup log dict
        log_dict = {
            "level": "Info",
            "action_text": "Email Delivery Failed ",
            "types": "Email Delivery",
            "target": target,
        }

        notify_helpers.send_email_with_body_from_setting_template(
            request=request,
            template="bounced_email_notification",
            subject="subject_bounced_email_notification",
            to=to,
            context={
                "target": target,
                "event": event,
            },
            log_dict=log_dict,
        )


def build_url_for_request(request=None, path="", query=None, fragment=""):
    """Builds a url from the base url relevant for the current request context
    :request: An instance of django.http.HTTPRequest
    :path: A str indicating the path
    :query: A dictionary with any GET parameters
    :fragment: A string indicating the fragment
    :return: An instance of urllib.parse.SplitResult
    """
    if request is None:
        request = get_current_request()

    return build_url(
        netloc=request.get_host(),
        scheme=request.scheme,
        path=path,
        query=query,
        fragment=fragment,
    )


def replace_netloc_port(netloc, new_port):
    return ":".join((netloc.split(":")[0], new_port))


def build_url(netloc, port=None, scheme=None, path="", query="", fragment=""):
    """Builds a url given all its parts
    :netloc: string
    :port: int
    :scheme: string
    :path: string
    :query: A dict or QueryDict with any GET parameters, or a query string with
        percent-encoded paramater values
    :fragment: string
    :return: URL string
    """

    # Percent-encode values inside query parameters.
    # Allow '/' to match Django template filter |urlencode default behavior.
    if query and isinstance(query, QueryDict):
        # Support multiple values for the same key
        query = query.urlencode(safe="/")
    elif query and isinstance(query, dict):
        query = urlencode(query, safe="/")

    if scheme is None:
        scheme = GlobalRequestMiddleware.get_current_request().scheme

    if port is not None:
        netloc = replace_netloc_port(netloc, port)

    return SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        query=query,
        fragment=fragment,
    ).geturl()


def get_current_request():
    try:
        return GlobalRequestMiddleware.get_current_request()
    except (KeyError, AttributeError):
        return None


def get_janeway_version():
    """Returns the installed version of janeway
    :return: `string` version
    """
    return str(janeway_version)


def get_log_entries(object):
    content_type = ContentType.objects.get_for_model(object)
    return models.LogEntry.objects.filter(
        content_type=content_type,
        object_id=object.pk,
    )


def _site_url_for(site, url_name, **kwargs):
    """Builds an absolute URL for a site object and a named URL."""
    path = reverse(url_name, kwargs=kwargs)
    return site.site_url(path=path)


def _journal_setting(journal, group, name, default=None):
    """Returns a journal setting value, or default when the setting doesn't exist."""
    try:
        return journal.get_setting(group, name)
    except Exception:
        return default


def _plain_label(text):
    """Strip HTML tags and decode entities to produce a plain-text sitemap label."""
    return html.unescape(strip_tags(text or ""))


def _accessibility_lastmod():
    """Last-modified date of the accessibility conformance data file.

    The /accessibility/ page is rendered from a11y/conformance_data.json, so
    its lastmod is the file's mtime.  Returns a timezone-aware UTC datetime,
    or None if the file is unavailable.
    """
    path = os.path.join(settings.BASE_DIR, "a11y", "conformance_data.json")
    try:
        return datetime.datetime.fromtimestamp(
            os.path.getmtime(path), tz=datetime.timezone.utc
        )
    except OSError:
        return None


def _build_clash_names(press):
    """Names shared by more than one entity in the press's full child set.

    Used at the press index level to decide when to disambiguate the press's
    own name and the names of its journals/repositories with [press] / [journal]
    / [repository] suffixes (WCAG 2.4.4 same-link-text).
    """
    from collections import Counter

    names = [press.name]
    for j in press.journals_az.filter(hide_from_press=False, is_remote=False):
        names.append(j.name)
    for r in repo_models.Repository.objects.filter(live=True):
        names.append(r.name)
    counts = Counter(names)
    return {name for name, count in counts.items() if count > 1}


def _local_clash_names(*names):
    """Names that appear more than once in the given list.

    Used at sub-press levels (journal, repo, sub-sitemaps) where only a small
    fixed set of entity names appears on a single page.
    """
    from collections import Counter

    counts = Counter(names)
    return {name for name, count in counts.items() if count > 1}


def _suffixed_name(name, clash_names, suffix):
    """name + suffix if name is in clash_names, else name unchanged."""
    if name in clash_names:
        return f"{name} {suffix}"
    return name


def _disambiguate_labels_by_date(entries):
    """Disambiguate clashing content labels using progressively finer date granularity.

    entries: list of dicts, each containing at least 'title' (str) and 'date'
    (date or datetime).  Modifies 'title' in-place for clashing groups.

    Tries [year], [Mon YYYY], [DD Mon YYYY] in turn; if still not unique, falls
    back to sequential [#1], [#2], ... assigned by ascending date (so oldest = #1
    and existing items keep their numbers as new ones are added).
    """
    from collections import defaultdict

    groups = defaultdict(list)
    for i, entry in enumerate(entries):
        groups[entry["title"].lower()].append((i, entry))

    for _lower_title, group in groups.items():
        if len(group) == 1:
            continue

        original_titles = {i: e["title"] for i, e in group}

        # Fallback when one or more entries have no date (e.g. canonical
        # pages clashing with CMS pages): number them in iteration order.
        if any(e.get("date") is None for _, e in group):
            for n, (i, entry) in enumerate(group, 1):
                entry["title"] = f"{original_titles[i]} [#{n}]"
            continue

        for fmt in [
            lambda d: str(d.year),
            lambda d: d.strftime("%b %Y"),
            lambda d: d.strftime("%d %b %Y"),
        ]:
            candidates = {i: fmt(e["date"]) for i, e in group}
            if len(set(candidates.values())) == len(group):
                for i, entry in group:
                    entry["title"] = f"{original_titles[i]} [{candidates[i]}]"
                break
        else:
            sorted_group = sorted(group, key=lambda t: t[1]["date"])
            numbered = {i: n for n, (i, _) in enumerate(sorted_group, 1)}
            for i, entry in group:
                entry["title"] = f"{original_titles[i]} [#{numbered[i]}]"

    return entries


def _published_cms_pages(owner):
    """Published (non-draft) CMS pages owned by `owner` (Press or Journal).

    Excludes pages with no meaningful content.  `content` is a modeltranslation
    field, so DB-level `content=""` filters do not reliably target the active
    column; check the rendered text in Python instead.  A page with only HTML
    wrapper tags (e.g. `<p></p>`) or whitespace is treated as empty.
    """
    owner_ct = ContentType.objects.get_for_model(owner)
    candidates = cms_models.Page.objects.filter(
        content_type=owner_ct,
        object_id=owner.pk,
        is_draft=False,
    )
    return [p for p in candidates if _plain_label(p.content).strip()]


def _cms_page_url(page, owner):
    """Absolute URL for a CMS page, scoped to its owner's site."""
    return owner.site_url(path=f"/site/{page.name}/")


def _cms_page_entries(owner):
    """[(url, label, lastmod), ...] for published CMS pages owned by `owner`."""
    return [
        (_cms_page_url(page, owner), page.display_name, page.edited)
        for page in _published_cms_pages(owner)
    ]


def _canonical_press_links(press):
    """Always-include links for the press pages sitemap."""
    links = [
        (_site_url_for(press, "website_index"), "Home", None),
        (
            _site_url_for(press, "accessibility"),
            "Accessibility",
            _accessibility_lastmod(),
        ),
    ]
    if press.publishes_journals and not press.disable_journals:
        links.append((_site_url_for(press, "press_journals"), "Journals", None))
    if press.publishes_conferences:
        links.append((_site_url_for(press, "press_conferences"), "Conferences", None))
    if press.active_news_items.exists():
        links.append((_site_url_for(press, "core_news_list"), "News", None))
    links.append((_site_url_for(press, "contact"), "Contact", None))
    links.append((_site_url_for(press, "core_login"), "Log in", None))
    links.append((_site_url_for(press, "core_register"), "Register", None))
    privacy_url = press.privacy_policy_url
    if privacy_url:
        if not urlparse(privacy_url).scheme:
            if not privacy_url.startswith("/"):
                privacy_url = f"/{privacy_url}"
            links.append((press.site_url(path=privacy_url), "Privacy Policy", None))
    else:
        links.append((press.site_url(path="/site/privacy/"), "Privacy Policy", None))
    return links


def _canonical_journal_links(journal):
    """Always-include links for a journal pages sitemap, gated by nav_* flags."""
    links = [
        (_site_url_for(journal, "website_index"), "Home", None),
        (
            _site_url_for(journal, "accessibility"),
            "Accessibility",
            _accessibility_lastmod(),
        ),
    ]
    if journal.nav_contact:
        links.append((_site_url_for(journal, "contact"), "Contact", None))
    if journal.nav_articles:
        links.append((_site_url_for(journal, "journal_articles"), "Articles", None))
    if journal.nav_issues:
        links.append((_site_url_for(journal, "journal_issues"), "Issues", None))
    if journal.nav_news and journal.active_news_items.exists():
        links.append((_site_url_for(journal, "core_news_list"), "News", None))
    if journal.nav_sub:
        links.append(
            (_site_url_for(journal, "journal_submissions"), "Submissions", None)
        )
    if journal.nav_start and not _journal_setting(
        journal, "general", "disable_journal_submission"
    ):
        links.append(
            (_site_url_for(journal, "submission_start"), "Start Submission", None)
        )
    if journal.nav_review:
        links.append(
            (
                _site_url_for(journal, "become_reviewer"),
                "Become a Reviewer",
                None,
            )
        )
    if _journal_setting(journal, "general", "enable_editorial_display"):
        editorial_label = _plain_label(
            _journal_setting(journal, "styling", "editorial_group_page_name")
            or "Editorial Team"
        )
        links.append((_site_url_for(journal, "editorial_team"), editorial_label, None))
    if _journal_setting(journal, "general", "keyword_list_page"):
        links.append((_site_url_for(journal, "keywords"), "Keyword List", None))
    links.append((_site_url_for(journal, "core_login"), "Log in", None))
    links.append((_site_url_for(journal, "core_register"), "Register", None))
    privacy_url = _journal_setting(journal, "general", "privacy_policy_url")
    if privacy_url:
        if not urlparse(privacy_url).scheme:
            if not privacy_url.startswith("/"):
                privacy_url = f"/{privacy_url}"
            links.append((journal.site_url(path=privacy_url), "Privacy Policy", None))
    else:
        links.append((journal.site_url(path="/site/privacy/"), "Privacy Policy", None))
    return links


def _canonical_repo_links(repo):
    """Always-include links for the repository pages sitemap."""
    return [
        (_site_url_for(repo, "website_index"), "Home", None),
        (
            _site_url_for(repo, "accessibility"),
            "Accessibility",
            _accessibility_lastmod(),
        ),
        (_site_url_for(repo, "repository_about"), "About", None),
        (
            _site_url_for(repo, "repository_list"),
            repo.object_name_plural.capitalize(),
            None,
        ),
        (_site_url_for(repo, "core_login"), "Log in", None),
        (_site_url_for(repo, "core_register"), "Register", None),
    ]


def _journal_regular_issues(journal):
    """Published Issue records of type 'issue' (excludes special collections)."""
    return journal.published_issues.filter(issue_type__code="issue")


def _articles_not_in_any_regular_issue(journal):
    """Published articles not assigned to any regular (non-collection) issue."""
    return submission_models.Article.objects.filter(
        journal=journal,
        stage=submission_models.STAGE_PUBLISHED,
        date_published__lte=timezone.now(),
    ).exclude(issues__issue_type__code="issue")


def _preprints_without_subject(repo):
    """Published preprints in `repo` with no assigned subject."""
    return repo_models.Preprint.objects.filter(
        repository=repo,
        stage=repo_models.STAGE_PREPRINT_PUBLISHED,
        subject__isnull=True,
    )


def build_pages_sitemap_context(owner):
    """Pages sub-sitemap context: canonicals + CMS pages, deduped by URL,
    sorted case-insensitively by label.

    On URL collision the canonical label wins (consistent, translatable later)
    but the CMS page's lastmod is kept.
    """
    if isinstance(owner, press_models.Press):
        canonical = _canonical_press_links(owner)
        sitemap_level = "press-pages"
    elif isinstance(owner, journal_models.Journal):
        canonical = _canonical_journal_links(owner)
        sitemap_level = "journal-pages"
    else:
        canonical = _canonical_repo_links(owner)
        sitemap_level = "repository-pages"

    cms_entries = (
        _cms_page_entries(owner)
        if isinstance(owner, (press_models.Press, journal_models.Journal))
        else []
    )

    by_url = {}
    for url, label, lastmod in canonical:
        by_url[url] = (label, lastmod)
    for url, label, lastmod in cms_entries:
        if url in by_url:
            existing_label, _ = by_url[url]
            by_url[url] = (existing_label, lastmod)
        else:
            by_url[url] = (label, lastmod)

    entries = [
        {"url": url, "title": label, "lastmod": lastmod, "date": lastmod}
        for url, (label, lastmod) in by_url.items()
    ]
    _disambiguate_labels_by_date(entries)
    entries.sort(key=lambda e: e["title"].lower())
    links = [(e["url"], e["title"], e["lastmod"]) for e in entries]

    parent_sitemap = {
        "loc": f"{owner.site_url()}/sitemap.xml",
        "label": owner.name,
    }
    page_title = f"Pages sitemap - {owner.name}"
    return {
        "owner": owner,
        "links": links,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": sitemap_level,
    }


def build_news_sitemap_context(owner):
    """News sub-sitemap context for a Press or Journal owner."""
    news_items = [
        {
            "url": item.url,
            "posted": item.posted,
            "title": _plain_label(item.title),
            "date": item.posted,
        }
        for item in owner.active_news_items.order_by("-posted")
    ]
    _disambiguate_labels_by_date(news_items)
    sitemap_level = (
        "press-news" if isinstance(owner, press_models.Press) else "journal-news"
    )
    parent_sitemap = {
        "loc": f"{owner.site_url()}/sitemap.xml",
        "label": owner.name,
    }
    page_title = f"News sitemap - {owner.name}"
    return {
        "owner": owner,
        "news_items": news_items,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": sitemap_level,
    }


def build_issue_sitemap_context(issue_or_none, journal):
    """Issue sub-sitemap context.  When issue_or_none is None, produces a
    'Not in any issue' virtual sitemap.
    """
    if issue_or_none is not None:
        articles_qs = issue_or_none.get_sorted_articles()
        page_title = (
            f"Sitemap - {issue_or_none.non_pretty_issue_identifier}, {journal.name}"
        )
        sitemap_level = "issue"
    else:
        articles_qs = _articles_not_in_any_regular_issue(journal).order_by("title")
        page_title = f"Sitemap - Not in any issue, {journal.name}"
        sitemap_level = "not-in-any-issue"

    article_entries = []
    for article in articles_qs:
        try:
            lastmod_dt = article.fast_last_modified_date()
        except Exception:
            lastmod_dt = article.date_published
        article_entries.append(
            {
                "url": article.url,
                "lastmod": lastmod_dt.isoformat() if lastmod_dt else "",
                "title": _plain_label(article.title),
                "date": article.date_published,
            }
        )
    _disambiguate_labels_by_date(article_entries)

    parent_sitemap = {
        "loc": f"{journal.site_url()}/sitemap.xml",
        "label": journal.name,
    }
    return {
        "issue": issue_or_none,
        "journal": journal,
        "article_entries": article_entries,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": sitemap_level,
    }


def build_subject_sitemap_context(subject_or_none, repo):
    """Subject sub-sitemap context.  When subject_or_none is None, produces a
    'Not in any subject' virtual sitemap.
    """
    if subject_or_none is not None:
        qs = subject_or_none.published_preprints()
        page_title = f"Sitemap - {subject_or_none.name}, {repo.name}"
        sitemap_level = "subject"
    else:
        qs = _preprints_without_subject(repo)
        page_title = f"Sitemap - Not in any subject, {repo.name}"
        sitemap_level = "not-in-any-subject"

    preprint_entries = []
    for preprint in qs:
        if preprint.date_updated:
            lastmod = preprint.date_updated.isoformat()
        elif preprint.date_published:
            lastmod = preprint.date_published.isoformat()
        else:
            lastmod = ""
        preprint_entries.append(
            {
                "url": preprint.url,
                "lastmod": lastmod,
                "title": _plain_label(preprint.title),
                "date": preprint.date_updated or preprint.date_published,
            }
        )
    _disambiguate_labels_by_date(preprint_entries)

    parent_sitemap = {
        "loc": f"{repo.site_url()}/sitemap.xml",
        "label": repo.name,
    }
    return {
        "subject": subject_or_none,
        "repo": repo,
        "preprint_entries": preprint_entries,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": sitemap_level,
    }


def build_press_index_context(press):
    """Press siteindex context: pages → news → journals → repositories."""
    journals = press.journals_az.filter(
        hide_from_press=False,
        is_remote=False,
    )
    repos = repo_models.Repository.objects.filter(live=True)
    clash_names = _build_clash_names(press)
    press_label = _suffixed_name(press.name, clash_names, "[press]")

    child_sitemaps = [
        {
            "loc": f"{press.site_url()}/pages_sitemap.xml",
            "label": f"{press_label} pages",
            "group": "pages",
        }
    ]
    if press.active_news_items.exists():
        child_sitemaps.append(
            {
                "loc": f"{press.site_url()}/news_sitemap.xml",
                "label": f"{press_label} news",
                "group": "news",
            }
        )
    for journal in sorted(journals, key=lambda j: j.name.lower()):
        child_sitemaps.append(
            {
                "loc": f"{journal.site_url()}/sitemap.xml",
                "label": _suffixed_name(journal.name, clash_names, "[journal]"),
                "group": "journals",
            }
        )
    for repo in sorted(repos, key=lambda r: r.name.lower()):
        child_sitemaps.append(
            {
                "loc": f"{repo.site_url()}/sitemap.xml",
                "label": _suffixed_name(repo.name, clash_names, "[repository]"),
                "group": "repositories",
            }
        )

    page_title = f"Sitemap - {press_label}"
    return {
        "press": press,
        "child_sitemaps": child_sitemaps,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": "press",
    }


def build_journal_index_context(journal):
    """Journal siteindex context: pages → news → issues (date desc) → not-in-any-issue."""
    press = journal.press
    clash_names = _local_clash_names(journal.name, press.name)
    journal_label = _suffixed_name(journal.name, clash_names, "[journal]")
    press_label = _suffixed_name(press.name, clash_names, "[press]")
    child_sitemaps = [
        {
            "loc": f"{journal.site_url()}/pages_sitemap.xml",
            "label": f"{journal_label} pages",
            "group": "pages",
        }
    ]
    if journal.active_news_items.exists():
        child_sitemaps.append(
            {
                "loc": f"{journal.site_url()}/news_sitemap.xml",
                "label": f"{journal_label} news",
                "group": "news",
            }
        )
    regular_issues = sorted(
        [
            i
            for i in _journal_regular_issues(journal)
            if i.get_sorted_articles().exists()
        ],
        key=lambda i: i.date,
        reverse=True,
    )
    for issue in regular_issues:
        child_sitemaps.append(
            {
                "loc": (
                    f"{journal.site_url()}"
                    f"{reverse('journal_sitemap', kwargs={'issue_id': issue.pk})}"
                ),
                "label": issue.non_pretty_issue_identifier,
                "group": "issues",
            }
        )
    if _articles_not_in_any_regular_issue(journal).exists():
        child_sitemaps.append(
            {
                "loc": (f"{journal.site_url()}{reverse('journal_no_issue_sitemap')}"),
                "label": "Not in any issue",
                "group": "issues",
            }
        )

    parent_sitemap = {
        "loc": f"{press.site_url()}/sitemap.xml",
        "label": press_label,
    }
    page_title = f"Sitemap - {journal_label}"
    return {
        "journal": journal,
        "site_name": journal_label,
        "child_sitemaps": child_sitemaps,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": "journal",
    }


def build_repo_index_context(repo):
    """Repository siteindex context: pages → subjects → not-in-any-subject."""
    press = repo.press
    clash_names = _local_clash_names(repo.name, press.name)
    repo_label = _suffixed_name(repo.name, clash_names, "[repository]")
    press_label = _suffixed_name(press.name, clash_names, "[press]")
    child_sitemaps = [
        {
            "loc": f"{repo.site_url()}/pages_sitemap.xml",
            "label": f"{repo_label} pages",
            "group": "pages",
        }
    ]
    for subject in repo.subject_set.all().order_by("name"):
        if subject.published_preprints().exists():
            child_sitemaps.append(
                {
                    "loc": (
                        f"{repo.site_url()}"
                        f"{reverse('repository_sitemap', kwargs={'subject_id': subject.pk})}"
                    ),
                    "label": subject.name,
                    "group": "subjects",
                }
            )
    if _preprints_without_subject(repo).exists():
        child_sitemaps.append(
            {
                "loc": (f"{repo.site_url()}{reverse('repository_no_subject_sitemap')}"),
                "label": "Not in any subject",
                "group": "subjects",
            }
        )

    parent_sitemap = {
        "loc": f"{press.site_url()}/sitemap.xml",
        "label": press_label,
    }
    page_title = f"Sitemap - {repo_label}"
    return {
        "repo": repo,
        "site_name": repo_label,
        "child_sitemaps": child_sitemaps,
        "parent_sitemap": parent_sitemap,
        "page_title": page_title,
        "h1": page_title,
        "sitemap_level": "repository",
    }


def generate_sitemap(
    file, press=None, journal=None, repository=None, issue=None, subject=None
):
    """Routes to the correct template + context builder for a given target."""
    template, context = None, None
    if press:
        template = "common/press_sitemap.xml"
        context = build_press_index_context(press)
    elif journal:
        template = "common/level2_sitemap.xml"
        context = build_journal_index_context(journal)
    elif repository:
        template = "common/level2_sitemap.xml"
        context = build_repo_index_context(repository)
    elif issue:
        template = "common/issue_sitemap.xml"
        context = build_issue_sitemap_context(issue, issue.journal)
    elif subject:
        template = "common/subject_sitemap.xml"
        context = build_subject_sitemap_context(subject, subject.repository)

    if template and context:
        content = render_to_string(template, context)
        file.write(content)
    else:
        return "Must pass a press, journal, issue, repository or subject object."


def get_sitemap_path(path_parts, file_name):
    path = os.path.join(
        settings.BASE_DIR,
        "files",
        "sitemaps",
        *path_parts,
    )
    if not os.path.exists(path):
        os.makedirs(path)

    return os.path.join(path, file_name)


def write_journal_sitemap(journal):
    file_path = get_sitemap_path(
        path_parts=[journal.code],
        file_name="sitemap.xml",
    )
    with open(file_path, "w") as f:
        generate_sitemap(f, journal=journal)


def write_issue_sitemap(issue):
    file_path = get_sitemap_path(
        path_parts=[issue.journal.code],
        file_name="{}_sitemap.xml".format(issue.pk),
    )
    with open(file_path, "w") as f:
        generate_sitemap(f, issue=issue)


def write_repository_sitemap(repository):
    file_path = get_sitemap_path(
        path_parts=[repository.code],
        file_name="sitemap.xml",
    )
    with open(file_path, "w") as f:
        generate_sitemap(f, repository=repository)


def write_subject_sitemap(subject):
    file_path = get_sitemap_path(
        path_parts=[subject.repository.code],
        file_name="{}_sitemap.xml".format(subject.pk),
    )
    with open(file_path, "w") as f:
        generate_sitemap(f, subject=subject)


def write_press_sitemap():
    press = press_models.Press.objects.all().first()
    file_path = get_sitemap_path(
        path_parts=[],
        file_name="sitemap.xml",
    )
    with open(file_path, "w") as f:
        generate_sitemap(f, press=press)


def write_pages_sitemap(owner):
    """Pages sub-sitemap for a Press, Journal, or Repository."""
    path_parts = [] if isinstance(owner, press_models.Press) else [owner.code]
    file_path = get_sitemap_path(
        path_parts=path_parts,
        file_name="pages_sitemap.xml",
    )
    context = build_pages_sitemap_context(owner)
    content = render_to_string("common/pages_sitemap.xml", context)
    with open(file_path, "w") as f:
        f.write(content)


def write_news_sitemap(owner):
    """News sub-sitemap for a Press or Journal."""
    path_parts = [] if isinstance(owner, press_models.Press) else [owner.code]
    file_path = get_sitemap_path(
        path_parts=path_parts,
        file_name="news_sitemap.xml",
    )
    context = build_news_sitemap_context(owner)
    content = render_to_string("common/news_sitemap.xml", context)
    with open(file_path, "w") as f:
        f.write(content)


def write_not_in_any_issue_sitemap(journal):
    """'Not in any issue' sub-sitemap for a journal."""
    file_path = get_sitemap_path(
        path_parts=[journal.code],
        file_name="no_issue_sitemap.xml",
    )
    context = build_issue_sitemap_context(None, journal)
    content = render_to_string("common/issue_sitemap.xml", context)
    with open(file_path, "w") as f:
        f.write(content)


def write_not_in_any_subject_sitemap(repo):
    """'Not in any subject' sub-sitemap for a repository."""
    file_path = get_sitemap_path(
        path_parts=[repo.code],
        file_name="no_subject_sitemap.xml",
    )
    context = build_subject_sitemap_context(None, repo)
    content = render_to_string("common/subject_sitemap.xml", context)
    with open(file_path, "w") as f:
        f.write(content)


def get_aware_datetime(unparsed_string, use_noon_if_no_time=True):
    """
    Takes any ISO 8601 compliant date or datetime string
    and returns an aware datetime object.
    If no time information passed,
    noon UTC is assumed.
    """

    import re
    from dateutil import parser as dateparser
    from django.utils.timezone import is_aware, make_aware

    if use_noon_if_no_time and re.fullmatch(
        "[0-9]{4}-[0-9]{2}-[0-9]{2}", unparsed_string
    ):
        unparsed_string += " 12:00"

    parsed_datetime = dateparser.parse(unparsed_string)

    if is_aware(parsed_datetime):
        return parsed_datetime
    else:
        return make_aware(parsed_datetime)


def get_janeway_patch_version():
    from janeway import __version__

    return f"{__version__.major}.{__version__.minor}.{__version__.patch}"


def add_query_parameters_to_url(original_url, new_params):
    """
    Parse a URL string and then safely update the query parameters.
    Then re-encode them into a query string and generate the final URL.
    :param original_url: the raw URL to be updated
    :param new_params: the dict or QueryDict of new query parameters to add
    """
    parsed_url = urlparse(original_url)
    parsed_query = QueryDict(parsed_url.query, mutable=True)
    parsed_query.update(new_params)

    # Treat / as safe to match the default behavior of
    # template filters such as |urlencode
    new_query_string = parsed_query.urlencode(safe="/")
    final_url = parsed_url._replace(query=new_query_string).geturl()
    return final_url
