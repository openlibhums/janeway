"""Ground-up sitemap test suite.

Architecture:

- ``SitemapChecks`` — generic predicates that **return booleans**, one per
  reusable concern (no duplicate URLs, title/h1 named, renders all locs,
  schema-valid, …). ``assert_sitemap`` runs the applicable checks and is the
  only place these booleans become assertions.
- ``SitemapScenario`` — ONE rich fixture (a press; journals covering
  normal/hidden/remote/conference/no-news; repos covering live/not-live with
  subjects, a published preprint and an orphan preprint; a regular issue with a
  published article). Every runner walks this single dataset.
- Per-type runner classes (``PressIndexTests`` etc.) own the assertions: each
  calls ``assert_sitemap`` for the generic checks and adds the type-specific
  assertions for that sitemap.

The pure-function unit tests (``_plain_label``, ``_disambiguate_labels_by_date``,
``_suffixed_name``), the footer ``page_sitemap_url`` tag tests and the XSLT a11y
test live in their own focused classes lower down.
"""

import functools
import io
import os
from unittest import mock

from bs4 import BeautifulSoup

from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse
from django.urls.base import clear_script_prefix
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from utils import logic
from utils.logic import (
    build_press_index_context,
    build_journal_index_context,
    build_repo_index_context,
    build_pages_sitemap_context,
    build_news_sitemap_context,
    build_issue_sitemap_context,
    build_subject_sitemap_context,
    _articles_not_in_any_regular_issue,
    _canonical_articles_for_issue,
    _canonical_issue,
    _plain_label,
    _suffixed_name,
    _disambiguate_labels_by_date,
)
from utils import setting_handler
from utils.testing import helpers

from cms import models as cms_models
from core import models as core_models
from journal import models as journal_models
from repository import models as repo_models
from submission import models as submission_models


# Schemas live in src/utils/schema/; this file is in src/utils/tests/.
_SCHEMA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema"
)


@functools.lru_cache(maxsize=None)
def _load_schema(filename):
    from lxml import etree

    return etree.XMLSchema(etree.parse(os.path.join(_SCHEMA_ROOT, filename)))


# ---------------------------------------------------------------------------
# Generic checks — pure predicates returning bool. Assertions live in the
# runners (via assert_sitemap), never here.
# ---------------------------------------------------------------------------


class SitemapChecks:
    """Reusable boolean checks for any sitemap context.

    The normaliser collapses every context shape to ``[(url, label), …]`` so a
    single set of predicates serves indexes, pages, news, issue and subject
    sitemaps alike.
    """

    # --- normaliser ---
    @staticmethod
    def _entries(ctx):
        if "links" in ctx:  # pages
            return [(url, label) for url, label, _lastmod in ctx["links"]]
        if "child_sitemaps" in ctx:  # index (press/journal/repo)
            return [(c["loc"], c["label"]) for c in ctx["child_sitemaps"]]
        for key in ("article_entries", "preprint_entries", "news_items"):
            if key in ctx:  # issue / subject / news
                return [(e["url"], e["title"]) for e in ctx[key]]
        return []

    def _urls(self, ctx):
        return [url for url, _label in self._entries(ctx)]

    def _labels(self, ctx):
        return [label for _url, label in self._entries(ctx)]

    def _rendered_locs(self, template, ctx):
        xml = render_to_string(template, ctx)
        soup = BeautifulSoup(xml, "xml")
        return {el.get_text(strip=True) for el in soup.find_all("loc")}

    # No URL appears more than once in the sitemap.
    def no_duplicate_urls(self, ctx):
        urls = self._urls(ctx)
        return len(urls) == len(set(urls))

    # page_title and h1 are non-empty and each contains the expected name(s).
    def title_and_h1_named(self, ctx, *expected):
        for field in ("page_title", "h1"):
            value = ctx.get(field) or ""
            if not value.strip():
                return False
            if any(substring not in value for substring in expected):
                return False
        return True

    # The context exposes the required keys.
    def has_keys(self, ctx, keys):
        return all(key in ctx for key in keys)

    # Entry labels are sorted case-insensitively.
    def labels_alphabetical(self, ctx):
        labels = self._labels(ctx)
        return labels == sorted(labels, key=str.lower)

    # The context declares the expected sitemap level.
    def sitemap_level_is(self, ctx, level):
        return ctx.get("sitemap_level") == level

    # Every entry is emitted as a <loc> in the rendered XML.
    def all_entries_render_locs(self, template, ctx):
        locs = self._rendered_locs(template, ctx)
        return all(url in locs for url in self._urls(ctx))

    # The rendered XML validates against the sitemaps.org schema.
    def validates_against_schema(self, schema, template, ctx):
        from lxml import etree

        xml_str = render_to_string(template, ctx)
        doc = etree.parse(io.BytesIO(xml_str.encode("utf-8")))
        return bool(schema.validate(doc))

    # No two entries share a label.
    def labels_unique(self, ctx):
        labels = self._labels(ctx)
        return len(labels) == len(set(labels))

    # The rendered XML parses and is single-encoded (no doubled "&amp;amp;").
    def xml_well_formed_and_escaped(self, template, ctx):
        from lxml import etree

        xml_str = render_to_string(template, ctx)
        try:
            etree.fromstring(xml_str.encode("utf-8"))
        except etree.XMLSyntaxError:
            return False
        # A double-encoded ampersand (&amp;amp;) signals an escaping bug.
        return "&amp;amp;" not in xml_str

    # Entries are ordered newest-first by date.
    def entries_ordered_by_date_desc(self, ctx):
        items = (
            ctx.get("news_items")
            or ctx.get("article_entries")
            or ctx.get("preprint_entries")
            or []
        )
        if not items:
            return True
        date_key = "posted" if "posted" in items[0] else "date"
        dates = [item.get(date_key) for item in items]
        return dates == sorted(dates, reverse=True)

    # --- battery: the runners call this; it is the only place booleans become
    # assertions. Each check runs in its own subTest so a failure names the
    # check and the sitemap level. ---
    def assert_sitemap(
        self,
        ctx,
        *,
        names,
        level,
        template,
        schema_kind,
        keys=None,
        alphabetical=False,
        ordered=False,
    ):
        schema = _load_schema(
            "sitemap.xsd.xml" if schema_kind == "urlset" else "siteindex.xsd.xml"
        )
        results = [
            ("no_duplicate_urls", self.no_duplicate_urls(ctx)),
            ("title_and_h1_named", self.title_and_h1_named(ctx, *names)),
            ("sitemap_level_is", self.sitemap_level_is(ctx, level)),
            ("all_entries_render_locs", self.all_entries_render_locs(template, ctx)),
            (
                "validates_against_schema",
                self.validates_against_schema(schema, template, ctx),
            ),
            ("labels_unique", self.labels_unique(ctx)),
            (
                "xml_well_formed_and_escaped",
                self.xml_well_formed_and_escaped(template, ctx),
            ),
        ]
        if keys is not None:
            results.append(("has_keys", self.has_keys(ctx, keys)))
        if alphabetical:
            results.append(("labels_alphabetical", self.labels_alphabetical(ctx)))
        if ordered:
            results.append(
                ("entries_ordered_by_date_desc", self.entries_ordered_by_date_desc(ctx))
            )
        for check, result in results:
            with self.subTest(check=check, level=level):
                self.assertTrue(result, f"{level}: {check} failed")


# ---------------------------------------------------------------------------
# The single shared fixture every runner walks.
# ---------------------------------------------------------------------------


class SitemapScenario:
    """One rich dataset covering the sitemap variations.

    Handles exposed for runners:
      press, press_news
      journal_normal (visible, hosted, regular issue + published article + news)
      journal_no_news, journal_hidden, journal_remote, journal_conference
      issue_regular, article_published
      repo_live, subject, preprint_with_subject, preprint_orphan
      repo_not_live
    """

    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        ContentType.objects.clear_cache()

        cls.press = helpers.create_press()

        # journal_normal = TST (fully configured); journal_no_news = TSA.
        cls.journal_normal, cls.journal_no_news = helpers.create_journals()
        cls.journal_normal = journal_models.Journal.objects.get(
            code="TST", domain="testserver"
        )

        cls.journal_hidden = cls._make_journal(
            "HID", "hidden.example.com", "Hidden Journal", hide_from_press=True
        )
        cls.journal_remote = cls._make_journal(
            "REM", "remote.example.com", "Remote Journal", is_remote=True
        )
        cls.journal_conference = cls._make_journal(
            "CON", "conf.example.com", "Conference One", is_conference=True
        )
        # is_archived is metadata ("no longer publishing"), not a visibility
        # flag — archived journals are still listed normally.
        cls.journal_archived = cls._make_journal(
            "ARC", "archived.example.com", "Archived Journal", is_archived=True
        )

        # News: press has one active item; journal_normal has several covering
        # the display window (future/expired excluded; start/end boundaries and
        # open-ended included) with distinct posted dates for ordering.
        cls.press_news = cls._make_news_item(cls.press, "Press News", posted=-1)
        # A second active press item (ordering) plus future/expired (excluded).
        cls.press_news_2 = cls._make_news_item(cls.press, "Press News Two", posted=-2)
        cls.press_news_future = cls._make_news_item(
            cls.press, "Press Future", start=7, posted=-1
        )
        cls.press_news_expired = cls._make_news_item(
            cls.press, "Press Expired", start=-30, end=-1, posted=-1
        )
        cls.news_active = cls._make_news_item(
            cls.journal_normal, "Active News", start=-1, posted=-1
        )
        cls.news_future = cls._make_news_item(
            cls.journal_normal, "Future News", start=7, posted=-1
        )
        cls.news_expired = cls._make_news_item(
            cls.journal_normal, "Expired News", start=-30, end=-1, posted=-1
        )
        cls.news_boundary_start = cls._make_news_item(
            cls.journal_normal, "Boundary Start", start=0, posted=-2
        )
        cls.news_boundary_end = cls._make_news_item(
            cls.journal_normal, "Boundary End", start=-10, end=0, posted=-3
        )
        cls.news_open_ended = cls._make_news_item(
            cls.journal_normal, "Open Ended", start=-2, end=None, posted=-4
        )

        # A regular issue with one published article on journal_normal.
        cls.issue_type, _ = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal_normal,
            code="issue",
            defaults={"pretty_name": "Issue", "custom_plural": "Issues"},
        )
        cls.issue_regular, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_normal,
            volume="1",
            issue="1",
            issue_title="V1 I1",
            issue_type=cls.issue_type,
            defaults={"date": timezone.now()},
        )
        cls.author = helpers.create_author(cls.journal_normal)
        cls.section, _ = submission_models.Section.objects.get_or_create(
            journal=cls.journal_normal, name="Test Section"
        )
        cls.article_published = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Published Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )
        cls.issue_regular.articles.add(cls.article_published)

        # An empty regular issue (no articles) — excluded from the index.
        cls.issue_empty, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_normal,
            volume="9",
            issue="9",
            issue_title="Empty Issue",
            issue_type=cls.issue_type,
            defaults={"date": timezone.now()},
        )
        # A published article in no issue at all — drives "Not in any issue".
        cls.article_orphan = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Orphan Published Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )

        # A second regular issue also holding the published article; the article
        # is canonical to issue_regular (its primary_issue), so issue_regular_b
        # is empty after canonicalisation.
        cls.issue_regular_b, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_normal,
            volume="1",
            issue="2",
            issue_title="V1 I2",
            issue_type=cls.issue_type,
            defaults={"date": timezone.now()},
        )
        cls.issue_regular_b.articles.add(cls.article_published)
        cls.article_published.primary_issue = cls.issue_regular
        cls.article_published.save()

        # Unpublished and future-dated articles in issue_regular — excluded.
        cls.article_unpublished = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Unpublished Article",
            stage=submission_models.STAGE_UNDER_REVIEW,
            section=cls.section,
        )
        cls.issue_regular.articles.add(cls.article_unpublished)
        cls.article_future = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Future Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() + timezone.timedelta(days=7),
            section=cls.section,
        )
        cls.issue_regular.articles.add(cls.article_future)

        # A collection (non-regular issue type). Collections are not regular
        # issues: an article only in a collection routes to "Not in any issue",
        # and a collection is never listed as an issue child of the index.
        cls.collection_type, _ = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal_normal,
            code="collection",
            defaults={"pretty_name": "Collection", "custom_plural": "Collections"},
        )
        cls.collection, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_normal,
            volume="0",
            issue="0",
            issue_title="A Collection",
            issue_type=cls.collection_type,
            defaults={"date": timezone.now()},
        )
        cls.article_collection_only = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Collection Only Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )
        cls.collection.articles.add(cls.article_collection_only)
        # article_published is in a regular issue AND this collection.
        cls.collection.articles.add(cls.article_published)

        # A second regular issue with an earlier date and its own canonical
        # article, so the index lists issues newest-first.
        cls.issue_regular_c, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_normal,
            volume="1",
            issue="3",
            issue_title="V1 I3",
            issue_type=cls.issue_type,
            defaults={"date": timezone.now() - timezone.timedelta(days=10)},
        )
        cls.article_in_c = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Article In C",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=2),
            section=cls.section,
        )
        cls.issue_regular_c.articles.add(cls.article_in_c)

        # An article in a regular issue whose primary_issue is a collection (a
        # non-regular issue): canonicalisation falls back to its first regular
        # issue (issue_regular).
        cls.article_primary_collection = submission_models.Article.objects.create(
            journal=cls.journal_normal,
            owner=cls.author,
            title="Primary Collection Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=3),
            section=cls.section,
        )
        cls.issue_regular.articles.add(cls.article_primary_collection)
        cls.collection.articles.add(cls.article_primary_collection)
        cls.article_primary_collection.primary_issue = cls.collection
        cls.article_primary_collection.save()

        # Repository: live, with a subject + published preprint, plus an orphan
        # published preprint (no subject).
        cls.repo_manager = helpers.create_user("sitemap_repo_mgr@example.com")
        cls.repo_author = helpers.create_user("sitemap_repo_author@example.com")
        cls.repo_live, cls.subject = helpers.create_repository(
            cls.press, [cls.repo_manager], []
        )
        cls.preprint_with_subject = cls._make_preprint(
            cls.repo_live,
            cls.repo_author,
            subject=cls.subject,
            title="Subject Preprint",
        )
        cls.preprint_orphan = cls._make_preprint(
            cls.repo_live, cls.repo_author, subject=None, title="Orphan Preprint"
        )
        # A subject with no published preprints — excluded from the index.
        cls.subject_empty, _ = repo_models.Subject.objects.get_or_create(
            repository=cls.repo_live,
            name="Empty Subject",
            slug="empty-subject",
            defaults={"enabled": True},
        )

        # Two subjects in clear alphabetical order with a preprint tagged to
        # both — it is canonical only to the alphabetically-first subject.
        cls.subject_alpha, _ = repo_models.Subject.objects.get_or_create(
            repository=cls.repo_live,
            name="Aardvark Subject",
            slug="aardvark-subject",
            defaults={"enabled": True},
        )
        cls.subject_zeta, _ = repo_models.Subject.objects.get_or_create(
            repository=cls.repo_live,
            name="Zeta Subject",
            slug="zeta-subject",
            defaults={"enabled": True},
        )
        cls.preprint_multi = cls._make_preprint(
            cls.repo_live, cls.repo_author, subject=None, title="Multi Subject Preprint"
        )
        cls.preprint_multi.subject.add(cls.subject_alpha, cls.subject_zeta)

        # An unpublished preprint tagged to the main subject — excluded.
        cls.preprint_unpublished = repo_models.Preprint.objects.create(
            repository=cls.repo_live,
            owner=cls.repo_author,
            stage=repo_models.STAGE_PREPRINT_REVIEW,
            title="Unpublished Preprint",
            abstract="Abstract.",
            comments_editor="",
            date_submitted=timezone.now(),
        )
        cls.preprint_unpublished.subject.add(cls.subject)

        cls.repo_not_live = repo_models.Repository.objects.create(
            press=cls.press,
            name="Archive Repository",
            short_name="archiverepo",
            object_name="Preprint",
            object_name_plural="Preprints",
            publisher="Test Publisher",
            live=False,
            domain="archive.example.com",
        )

        # A live repo whose every published preprint has a subject — no orphan,
        # so its index carries no "Not in any subject" child.
        cls.repo_no_orphans = repo_models.Repository.objects.create(
            press=cls.press,
            name="Tidy Repository",
            short_name="tidyrepo",
            object_name="Preprint",
            object_name_plural="Preprints",
            publisher="Test Publisher",
            live=True,
            domain="tidy.example.com",
        )
        cls.repo_no_orphans_subject, _ = repo_models.Subject.objects.get_or_create(
            repository=cls.repo_no_orphans,
            name="Tidy Subject",
            slug="tidy-subject",
            defaults={"enabled": True},
        )
        cls._make_preprint(
            cls.repo_no_orphans,
            cls.repo_author,
            subject=cls.repo_no_orphans_subject,
            title="Tidy Preprint",
        )

        # CMS pages covering inclusion/exclusion and a canonical URL collision.
        cls.press_cms_visible = cls._make_cms_page(
            cls.press, "about-us", "About Us", "<p>About the press.</p>"
        )
        cls.press_cms_draft = cls._make_cms_page(
            cls.press, "draft-page", "Draft Page", "<p>Hidden.</p>", is_draft=True
        )
        cls.press_cms_empty = cls._make_cms_page(
            cls.press, "empty-page", "Empty Page", "<p></p>"
        )
        cls.press_cms_nbsp = cls._make_cms_page(
            cls.press, "nbsp-page", "Nbsp Page", "<p>&nbsp;</p>"
        )
        cls.press_cms_whitespace = cls._make_cms_page(
            cls.press, "whitespace-page", "Whitespace Page", "   \n\t  "
        )
        # name="privacy" → /site/privacy/ collides with the Privacy Policy
        # canonical; the CMS page must win both label and lastmod.
        cls.press_cms_privacy = cls._make_cms_page(
            cls.press, "privacy", "Privacy (CMS)", "<p>Our privacy policy.</p>"
        )
        cls.journal_cms_visible = cls._make_cms_page(
            cls.journal_normal, "journal-about", "Journal About", "<p>About.</p>"
        )

    # --- fixture helpers ---
    @classmethod
    def _make_journal(cls, code, domain, name, **flags):
        journal = journal_models.Journal.objects.create(code=code, domain=domain)
        journal.name = name
        for attr, value in flags.items():
            setattr(journal, attr, value)
        journal.save()
        return journal

    @classmethod
    def _make_news_item(cls, owner, title, start=-1, end=None, posted=-1):
        """start/end are day offsets for start_display/end_display (None end =
        open-ended); posted is a day offset for the posted datetime."""
        ContentType.objects.clear_cache()
        item = helpers.create_news_item(
            ContentType.objects.get_for_model(owner), owner.pk, title=title
        )
        today = timezone.now().date()
        item.start_display = today + timezone.timedelta(days=start)
        item.end_display = (
            today + timezone.timedelta(days=end) if end is not None else None
        )
        item.posted = timezone.now() + timezone.timedelta(days=posted)
        item.save()
        return item

    @classmethod
    def _make_cms_page(cls, owner, name, display_name, content, is_draft=False):
        return cms_models.Page.objects.create(
            content_type=ContentType.objects.get_for_model(owner),
            object_id=owner.pk,
            name=name,
            display_name=display_name,
            content=content,
            is_draft=is_draft,
        )

    @classmethod
    def _make_preprint(cls, repo, author, subject, title):
        preprint = repo_models.Preprint.objects.create(
            repository=repo,
            owner=author,
            stage=repo_models.STAGE_PREPRINT_PUBLISHED,
            title=title,
            abstract="Abstract.",
            comments_editor="",
            date_submitted=timezone.now(),
            date_published=timezone.now() - timezone.timedelta(hours=1),
        )
        if subject is not None:
            preprint.subject.add(subject)
        return preprint


# ---------------------------------------------------------------------------
# Runner: Press index
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class PressIndexTests(SitemapScenario, SitemapChecks, TestCase):
    """The press siteindex: pages → news → journals → repositories."""

    def _ctx(self):
        return build_press_index_context(self.press)

    def _locs(self, group):
        return [c["loc"] for c in self._ctx()["child_sitemaps"] if c["group"] == group]

    def test_press_index_battery(self):
        self.assert_sitemap(
            self._ctx(),
            names=[self.press.name],
            level="press",
            template="common/press_sitemap.xml",
            schema_kind="siteindex",
            keys=["press", "child_sitemaps", "page_title", "h1", "sitemap_level"],
        )

    def test_news_child_present_when_active_news(self):
        groups = [c["group"] for c in self._ctx()["child_sitemaps"]]
        self.assertIn("news", groups)

    def test_visible_journal_included(self):
        self.assertIn(
            f"{self.journal_normal.site_url()}/sitemap.xml", self._locs("journals")
        )

    def test_hidden_journal_excluded(self):
        self.assertNotIn(
            f"{self.journal_hidden.site_url()}/sitemap.xml", self._locs("journals")
        )

    def test_remote_journal_excluded(self):
        self.assertNotIn(
            f"{self.journal_remote.site_url()}/sitemap.xml", self._locs("journals")
        )

    def test_conference_included(self):
        self.assertIn(
            f"{self.journal_conference.site_url()}/sitemap.xml", self._locs("journals")
        )

    def test_live_repo_included(self):
        self.assertIn(
            f"{self.repo_live.site_url()}/sitemap.xml", self._locs("repositories")
        )

    def test_non_live_repo_excluded(self):
        self.assertNotIn(
            f"{self.repo_not_live.site_url()}/sitemap.xml", self._locs("repositories")
        )

    def test_name_clash_suffixes_press_and_journal(self):
        # When the press shares a journal's name, the press's own H1/title and
        # the clashing journal child are disambiguated.
        original = self.press.name
        self.press.name = self.journal_normal.name
        try:
            ctx = self._ctx()
            self.assertIn("[press]", ctx["page_title"])
            self.assertIn("[press]", ctx["h1"])
            journal_labels = [
                c["label"] for c in ctx["child_sitemaps"] if c["group"] == "journals"
            ]
            self.assertTrue(
                any(label.endswith("[journal]") for label in journal_labels),
                journal_labels,
            )
        finally:
            self.press.name = original

    def test_name_clash_suffixes_press_and_repo(self):
        # The press clash set includes live repo names, so a press sharing a
        # repo's name disambiguates the press H1/title and the repo child.
        original = self.press.name
        self.press.name = self.repo_live.name
        try:
            ctx = self._ctx()
            self.assertIn("[press]", ctx["page_title"])
            repo_labels = [
                c["label"]
                for c in ctx["child_sitemaps"]
                if c["group"] == "repositories"
            ]
            self.assertTrue(
                any(label.endswith("[repository]") for label in repo_labels),
                repo_labels,
            )
        finally:
            self.press.name = original

    def test_archived_journal_included(self):
        self.assertIn(
            f"{self.journal_archived.site_url()}/sitemap.xml", self._locs("journals")
        )

    def test_news_child_absent_when_no_news(self):
        self.press.active_news_items.all().delete()
        groups = [c["group"] for c in self._ctx()["child_sitemaps"]]
        self.assertNotIn("news", groups)

    def test_child_order(self):
        # Order: pages → news → journals (sorted) → repositories (sorted).
        children = self._ctx()["child_sitemaps"]
        groups = [c["group"] for c in children]
        self.assertEqual(groups[0], "pages")
        self.assertEqual(groups[1], "news")
        journal_pos = [i for i, g in enumerate(groups) if g == "journals"]
        repo_pos = [i for i, g in enumerate(groups) if g == "repositories"]
        self.assertLess(max(journal_pos), min(repo_pos))
        journal_labels = [c["label"] for c in children if c["group"] == "journals"]
        self.assertEqual(journal_labels, sorted(journal_labels, key=str.lower))
        repo_labels = [c["label"] for c in children if c["group"] == "repositories"]
        self.assertEqual(repo_labels, sorted(repo_labels, key=str.lower))


# ---------------------------------------------------------------------------
# Runner: Journal index
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class JournalIndexTests(SitemapScenario, SitemapChecks, TestCase):
    """A journal siteindex: pages → news → issues → not-in-any-issue."""

    def _ctx(self, journal=None):
        return build_journal_index_context(journal or self.journal_normal)

    def _children(self, group, journal=None):
        return [c for c in self._ctx(journal)["child_sitemaps"] if c["group"] == group]

    def test_journal_index_battery(self):
        self.assert_sitemap(
            self._ctx(),
            names=[self.journal_normal.name],
            level="journal",
            template="common/level2_sitemap.xml",
            schema_kind="siteindex",
            keys=[
                "journal",
                "site_name",
                "child_sitemaps",
                "parent_sitemap",
                "note",
                "page_title",
                "h1",
                "sitemap_level",
            ],
        )

    def test_visible_journal_links_to_press(self):
        ctx = self._ctx()
        self.assertIsNotNone(ctx["parent_sitemap"])
        self.assertFalse(ctx["note"])
        self.assertEqual(ctx["parent_sitemap"]["label"], self.press.name)

    def test_hidden_journal_has_no_parent_and_note(self):
        ctx = self._ctx(self.journal_hidden)
        self.assertIsNone(ctx["parent_sitemap"])
        self.assertIn("hidden", ctx["note"].lower())

    def test_news_child_present(self):
        self.assertTrue(self._children("news"))

    def test_regular_issue_with_articles_included(self):
        locs = [c["loc"] for c in self._children("issues")]
        self.assertTrue(any(str(self.issue_regular.pk) in loc for loc in locs))

    def test_empty_issue_excluded(self):
        locs = [c["loc"] for c in self._children("issues")]
        self.assertFalse(any(str(self.issue_empty.pk) in loc for loc in locs))

    def test_not_in_any_issue_child_present_with_orphan(self):
        labels = [c["label"] for c in self._ctx()["child_sitemaps"]]
        self.assertIn("Not in any issue", labels)

    def test_children_carry_group(self):
        self.assertTrue(all("group" in c for c in self._ctx()["child_sitemaps"]))

    def test_name_clash_suffixes_journal_and_parent(self):
        # When a visible journal shares the press name, its H1/title and the
        # press back-link are disambiguated. Journal.press is a property that
        # re-fetches Press.objects.first(), so the clash must be persisted (the
        # test transaction rolls it back afterwards).
        self.press.name = self.journal_normal.name
        self.press.save()
        ctx = build_journal_index_context(self.journal_normal)
        self.assertIn("[journal]", ctx["page_title"])
        self.assertIn("[journal]", ctx["h1"])
        self.assertIn("[press]", ctx["parent_sitemap"]["label"])

    def test_news_child_absent_when_no_news(self):
        groups = [c["group"] for c in self._ctx(self.journal_no_news)["child_sitemaps"]]
        self.assertNotIn("news", groups)

    def test_no_issue_child_absent_without_orphans(self):
        labels = [c["label"] for c in self._ctx(self.journal_no_news)["child_sitemaps"]]
        self.assertNotIn("Not in any issue", labels)

    def test_collection_not_listed_as_issue_child(self):
        # Collections (non-regular issue types) are never index children.
        locs = [c["loc"] for c in self._children("issues")]
        self.assertFalse(any(str(self.collection.pk) in loc for loc in locs))

    def test_hidden_journal_applies_no_name_clash_suffix(self):
        # A hidden journal carries no press reference on its page, so even a
        # name clash with the press applies no [journal]/[press] suffix.
        self.press.name = self.journal_hidden.name
        self.press.save()
        ctx = build_journal_index_context(self.journal_hidden)
        self.assertIsNone(ctx["parent_sitemap"])
        self.assertNotIn("[journal]", ctx["page_title"])
        self.assertNotIn("[journal]", ctx["h1"])

    def test_child_order(self):
        # Order: pages → news → issues (date desc) → not-in-any-issue.
        children = self._ctx()["child_sitemaps"]
        groups = [c["group"] for c in children]
        self.assertEqual(groups[0], "pages")
        self.assertEqual(groups[1], "news")
        # Regular issues are listed newest-first (issue_regular before the
        # earlier-dated issue_regular_c).
        issue_locs = [c["loc"] for c in children if c["group"] == "issues"]
        pos_regular = next(
            i for i, loc in enumerate(issue_locs) if str(self.issue_regular.pk) in loc
        )
        pos_c = next(
            i for i, loc in enumerate(issue_locs) if str(self.issue_regular_c.pk) in loc
        )
        self.assertLess(pos_regular, pos_c)
        # "Not in any issue" is the last child.
        self.assertEqual(children[-1]["label"], "Not in any issue")


# ---------------------------------------------------------------------------
# Runner: Repository index
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class RepoIndexTests(SitemapScenario, SitemapChecks, TestCase):
    """A repository siteindex: pages → subjects → not-in-any-subject."""

    def _ctx(self):
        return build_repo_index_context(self.repo_live)

    def _children(self, group):
        return [c for c in self._ctx()["child_sitemaps"] if c["group"] == group]

    def test_repo_index_battery(self):
        self.assert_sitemap(
            self._ctx(),
            names=[self.repo_live.name],
            level="repository",
            template="common/level2_sitemap.xml",
            schema_kind="siteindex",
            keys=[
                "repo",
                "site_name",
                "child_sitemaps",
                "parent_sitemap",
                "page_title",
                "h1",
                "sitemap_level",
            ],
        )

    def test_links_to_press(self):
        self.assertEqual(self._ctx()["parent_sitemap"]["label"], self.press.name)

    def test_subject_with_preprints_included(self):
        locs = [c["loc"] for c in self._children("subjects")]
        self.assertTrue(any(str(self.subject.pk) in loc for loc in locs))

    def test_empty_subject_excluded(self):
        locs = [c["loc"] for c in self._children("subjects")]
        self.assertFalse(any(str(self.subject_empty.pk) in loc for loc in locs))

    def test_not_in_any_subject_child_present_with_orphan(self):
        labels = [c["label"] for c in self._ctx()["child_sitemaps"]]
        self.assertIn("Not in any subject", labels)

    def test_children_carry_group(self):
        self.assertTrue(all("group" in c for c in self._ctx()["child_sitemaps"]))

    def test_name_clash_suffixes_repo_and_parent(self):
        repo = self.repo_live
        press = repo.press
        original = press.name
        press.name = repo.name
        try:
            ctx = build_repo_index_context(repo)
            self.assertIn("[repository]", ctx["page_title"])
            self.assertIn("[repository]", ctx["h1"])
            self.assertIn("[press]", ctx["parent_sitemap"]["label"])
        finally:
            press.name = original

    def test_no_subject_child_absent_without_orphans(self):
        labels = [
            c["label"]
            for c in build_repo_index_context(self.repo_no_orphans)["child_sitemaps"]
        ]
        self.assertNotIn("Not in any subject", labels)

    def test_child_order(self):
        # Order: pages → subjects (alphabetical) → not-in-any-subject.
        children = self._ctx()["child_sitemaps"]
        self.assertEqual(children[0]["group"], "pages")
        subject_labels = [
            c["label"]
            for c in children
            if c["group"] == "subjects" and c["label"] != "Not in any subject"
        ]
        self.assertEqual(subject_labels, sorted(subject_labels, key=str.lower))
        self.assertEqual(children[-1]["label"], "Not in any subject")


# ---------------------------------------------------------------------------
# Runner: Pages sub-sitemaps (press / journal / repo) — canonicals + CMS
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class PagesSitemapTests(SitemapScenario, SitemapChecks, TestCase):
    """Pages sub-sitemaps: canonical links + published CMS pages, deduped by
    URL (CMS wins on collision), sorted case-insensitively by label."""

    TEMPLATE = "common/pages_sitemap.xml"

    def _ctx(self, owner):
        return build_pages_sitemap_context(owner)

    def _entry_by_url(self, owner, url):
        for link_url, label, lastmod in self._ctx(owner)["links"]:
            if link_url == url:
                return (label, lastmod)
        return None

    def _entry_by_label(self, owner, label):
        for link_url, link_label, lastmod in self._ctx(owner)["links"]:
            if link_label == label:
                return (link_url, lastmod)
        return None

    @staticmethod
    def _cms_url(owner, name):
        return owner.site_url(path=f"/site/{name}/")

    # --- generic battery across all three owners ---
    def test_pages_battery(self):
        cases = [
            (self.press, "press-pages"),
            (self.journal_normal, "journal-pages"),
            (self.repo_live, "repository-pages"),
        ]
        for owner, level in cases:
            with self.subTest(owner=level):
                self.assert_sitemap(
                    self._ctx(owner),
                    names=[owner.name],
                    level=level,
                    template=self.TEMPLATE,
                    schema_kind="urlset",
                    keys=[
                        "owner",
                        "links",
                        "parent_sitemap",
                        "page_title",
                        "h1",
                        "sitemap_level",
                    ],
                    alphabetical=True,
                )

    # --- CMS page inclusion ---
    def test_cms_visible_page_included_with_display_name_and_edited(self):
        entry = self._entry_by_url(self.press, self._cms_url(self.press, "about-us"))
        self.assertIsNotNone(entry)
        label, lastmod = entry
        self.assertEqual(label, self.press_cms_visible.display_name)
        self.assertEqual(lastmod, self.press_cms_visible.edited)

    def test_cms_draft_excluded(self):
        self.assertIsNone(
            self._entry_by_url(self.press, self._cms_url(self.press, "draft-page"))
        )

    def test_cms_empty_content_excluded(self):
        self.assertIsNone(
            self._entry_by_url(self.press, self._cms_url(self.press, "empty-page"))
        )

    def test_cms_nbsp_only_content_excluded(self):
        self.assertIsNone(
            self._entry_by_url(self.press, self._cms_url(self.press, "nbsp-page"))
        )

    def test_cms_whitespace_only_content_excluded(self):
        self.assertIsNone(
            self._entry_by_url(self.press, self._cms_url(self.press, "whitespace-page"))
        )

    def test_cms_scoping_press_page_absent_from_journal(self):
        # content_type scoping: a press CMS page must not leak into a journal.
        self.assertIsNone(
            self._entry_by_url(
                self.journal_normal, self._cms_url(self.press, "about-us")
            )
        )

    # --- URL collision: a CMS page wins label + lastmod over a canonical ---
    def test_cms_collision_cms_wins_label_and_lastmod(self):
        url = self._cms_url(self.press, "privacy")  # == Privacy Policy canonical
        entry = self._entry_by_url(self.press, url)
        self.assertIsNotNone(entry)
        label, lastmod = entry
        self.assertEqual(label, self.press_cms_privacy.display_name)
        self.assertEqual(lastmod, self.press_cms_privacy.edited)

    # --- lastmod sources ---
    def test_static_canonical_has_no_lastmod(self):
        entry = self._entry_by_label(self.press, "Home")
        self.assertIsNotNone(entry)
        self.assertIsNone(entry[1])

    def test_accessibility_lastmod_is_file_mtime(self):
        entry = self._entry_by_label(self.press, "Accessibility")
        self.assertIsNotNone(entry)
        self.assertEqual(entry[1], logic._accessibility_lastmod())

    # --- Privacy Policy URL: relative path used, absolute/external omitted ---
    def test_privacy_relative_url_used(self):
        self.press.privacy_policy_url = "/custom-privacy/"
        self.press.save()
        try:
            entry = self._entry_by_label(self.press, "Privacy Policy")
            self.assertIsNotNone(entry)
            self.assertIn("/custom-privacy/", entry[0])
        finally:
            self.press.privacy_policy_url = ""
            self.press.save()

    def test_privacy_absolute_url_omitted(self):
        # A sitemap may only list same-host URLs, so an absolute/external privacy
        # URL is dropped rather than linked.
        self.press.privacy_policy_url = "https://external.example.com/privacy/"
        self.press.save()
        try:
            self.assertNotIn("Privacy Policy", self._labels_for(self.press))
            urls = [url for url, _label, _lastmod in self._ctx(self.press)["links"]]
            self.assertFalse(any("external.example.com" in url for url in urls))
        finally:
            self.press.privacy_policy_url = ""
            self.press.save()

    # --- pages sitemap_level ---
    def test_pages_levels(self):
        for owner, level in (
            (self.press, "press-pages"),
            (self.journal_normal, "journal-pages"),
            (self.repo_live, "repository-pages"),
        ):
            with self.subTest(level=level):
                self.assertTrue(self.sitemap_level_is(self._ctx(owner), level))

    # --- News canonical link: gated by active news, not by nav_news ---
    def _labels_for(self, owner):
        return [label for _url, label, _lastmod in self._ctx(owner)["links"]]

    def test_news_canonical_present_when_active_news(self):
        self.assertIn("News", self._labels_for(self.journal_normal))

    def test_news_canonical_absent_when_no_news(self):
        self.assertNotIn("News", self._labels_for(self.journal_no_news))

    def test_nav_news_does_not_gate_news_canonical(self):
        # journal_normal has active news but nav_news defaults to False; the
        # /news/ URL is always served, so the canonical must still be listed.
        self.assertFalse(self.journal_normal.nav_news)
        self.assertIn("News", self._labels_for(self.journal_normal))

    # --- canonical-link gating by settings / nav_* flags ---
    def test_home_and_accessibility_always_present(self):
        for owner in (self.press, self.journal_normal, self.repo_live):
            with self.subTest(owner=owner.code):
                labels = self._labels_for(owner)
                self.assertIn("Home", labels)
                self.assertIn("Accessibility", labels)

    def test_press_journals_canonical_gated_by_disable_journals(self):
        # publishes_journals is true (the press has hosted journals), so the
        # link shows unless journals are disabled.
        self.assertIn("Journals", self._labels_for(self.press))
        self.press.disable_journals = True
        self.press.save()
        try:
            self.assertNotIn("Journals", self._labels_for(self.press))
        finally:
            self.press.disable_journals = False
            self.press.save()

    def test_press_conferences_canonical_present_when_publishing(self):
        # The fixture has a conference, so publishes_conferences is true.
        self.assertIn("Conferences", self._labels_for(self.press))

    def test_journal_nav_flags_gate_canonicals(self):
        cases = [
            ("nav_contact", "Contact"),
            ("nav_articles", "Articles"),
            ("nav_issues", "Issues"),
            ("nav_sub", "Submissions"),
            ("nav_review", "Become a Reviewer"),
            ("nav_start", "Start Submission"),
        ]
        journal = self.journal_normal
        for field, label in cases:
            with self.subTest(field=field):
                self.assertIn(label, self._labels_for(journal))  # present by default
                original = getattr(journal, field)
                setattr(journal, field, False)
                journal.save()
                try:
                    self.assertNotIn(label, self._labels_for(journal))
                finally:
                    setattr(journal, field, original)
                    journal.save()

    def test_press_always_present_canonicals(self):
        # (Privacy Policy is also always present, but the fixture's "privacy"
        # CMS page collides with it and wins the label — covered by
        # test_cms_collision_cms_wins_label_and_lastmod.)
        labels = self._labels_for(self.press)
        for label in ("Home", "Accessibility", "Contact", "Log in", "Register"):
            with self.subTest(label=label):
                self.assertIn(label, labels)

    def test_repo_always_present_canonicals(self):
        labels = self._labels_for(self.repo_live)
        # The "list" link is labelled with the repo's object_name_plural.
        expected = [
            "Home",
            "Accessibility",
            "About",
            "Log in",
            "Register",
            self.repo_live.object_name_plural.capitalize(),
        ]
        for label in expected:
            with self.subTest(label=label):
                self.assertIn(label, labels)

    def test_journal_editorial_canonical_gated_by_setting(self):
        journal = self.journal_normal
        self.assertNotIn("Editorial Team", self._labels_for(journal))  # default off
        setting_handler.save_setting(
            "general", "enable_editorial_display", journal, "on"
        )
        try:
            self.assertIn("Editorial Team", self._labels_for(journal))
        finally:
            setting_handler.save_setting(
                "general", "enable_editorial_display", journal, ""
            )

    def test_journal_keyword_list_canonical_gated_by_setting(self):
        journal = self.journal_normal
        self.assertNotIn("Keyword List", self._labels_for(journal))  # default off
        setting_handler.save_setting("general", "keyword_list_page", journal, "on")
        try:
            self.assertIn("Keyword List", self._labels_for(journal))
        finally:
            setting_handler.save_setting("general", "keyword_list_page", journal, "")


# ---------------------------------------------------------------------------
# Editorial links in the pages sitemap: per-group under multi_page_editorial,
# aggregate fallback when no groups exist, and never a stale cached list.
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="domain")
class SitemapEditorialTests(TestCase):
    """The journal pages sitemap editorial links must be per-group and fresh."""

    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        cls.press = helpers.create_press()
        cls.journal, cls.empty_journal = helpers.create_journals()
        for journal in (cls.journal, cls.empty_journal):
            setting_handler.save_setting(
                "general", "enable_editorial_display", journal, "on"
            )
            setting_handler.save_setting(
                "styling", "multi_page_editorial", journal, "on"
            )
        # cls.journal has groups; cls.empty_journal deliberately has none so the
        # zero-groups fallback can be exercised.
        cls.group_one = core_models.EditorialGroup.objects.create(
            name="Editorial Board",
            press=cls.press,
            journal=cls.journal,
            sequence=1,
        )
        cls.group_two = core_models.EditorialGroup.objects.create(
            name="Advisory Board",
            press=cls.press,
            journal=cls.journal,
            sequence=2,
        )

    def sitemap_urls(self, owner):
        return [
            url for url, _label, _lastmod in build_pages_sitemap_context(owner)["links"]
        ]

    def test_multi_page_editorial_lists_one_url_per_group(self):
        urls = self.sitemap_urls(self.journal)
        for group in (self.group_one, self.group_two):
            with self.subTest(group=group.name):
                group_path = reverse(
                    "editorial_team_group", kwargs={"group_id": group.pk}
                )
                self.assertTrue(
                    any(group_path in url for url in urls),
                    "per-group editorial page dropped from the journal sitemap "
                    "when multi_page_editorial is enabled",
                )

    def test_multi_page_editorial_without_groups_falls_back_to_team_link(self):
        urls = self.sitemap_urls(self.empty_journal)
        team_path = reverse("editorial_team")
        self.assertTrue(
            any(team_path in url for url in urls),
            "multi_page_editorial with no groups dropped the editorial link "
            "entirely instead of linking the aggregate team page",
        )

    def test_added_group_appears_without_stale_cache(self):
        # The sitemap must query editorial groups directly, not via the
        # @cache(300) journal.editorial_groups(): a group added after a first
        # build must appear on the next build.
        self.assertNotIn(
            "New Board",
            [
                label
                for _url, label, _lastmod in build_pages_sitemap_context(self.journal)[
                    "links"
                ]
            ],
        )
        group_three = core_models.EditorialGroup.objects.create(
            name="New Board",
            press=self.press,
            journal=self.journal,
            sequence=3,
        )
        urls = self.sitemap_urls(self.journal)
        group_path = reverse(
            "editorial_team_group", kwargs={"group_id": group_three.pk}
        )
        self.assertTrue(
            any(group_path in url for url in urls),
            "a newly added editorial group was missing from the sitemap, "
            "indicating a stale cached group list",
        )


# ---------------------------------------------------------------------------
# Runner: News sub-sitemaps (press / journal)
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class NewsSitemapTests(SitemapScenario, SitemapChecks, TestCase):
    """News sub-sitemaps: active items only (display-window gated), newest first."""

    TEMPLATE = "common/news_sitemap.xml"

    def _ctx(self, owner):
        return build_news_sitemap_context(owner)

    def _titles(self, owner):
        return [item["title"] for item in self._ctx(owner)["news_items"]]

    def test_news_battery(self):
        for owner, level in (
            (self.press, "press-news"),
            (self.journal_normal, "journal-news"),
        ):
            with self.subTest(level=level):
                self.assert_sitemap(
                    self._ctx(owner),
                    names=[owner.name],
                    level=level,
                    template=self.TEMPLATE,
                    schema_kind="urlset",
                    keys=[
                        "owner",
                        "news_items",
                        "parent_sitemap",
                        "page_title",
                        "h1",
                        "sitemap_level",
                    ],
                    ordered=True,
                )

    def test_future_dated_excluded(self):
        self.assertNotIn("Future News", self._titles(self.journal_normal))

    def test_expired_excluded(self):
        self.assertNotIn("Expired News", self._titles(self.journal_normal))

    def test_window_boundaries_included(self):
        titles = self._titles(self.journal_normal)
        self.assertIn("Boundary Start", titles)
        self.assertIn("Boundary End", titles)

    def test_open_ended_included(self):
        self.assertIn("Open Ended", self._titles(self.journal_normal))

    def test_press_future_excluded(self):
        self.assertNotIn("Press Future", self._titles(self.press))

    def test_press_expired_excluded(self):
        self.assertNotIn("Press Expired", self._titles(self.press))

    def test_press_active_items_present(self):
        titles = self._titles(self.press)
        self.assertIn("Press News", titles)
        self.assertIn("Press News Two", titles)

    def test_news_content_type_scoping(self):
        # Press and journal news are scoped by content_type — neither owner's
        # items leak into the other's sitemap.
        press_titles = self._titles(self.press)
        journal_titles = self._titles(self.journal_normal)
        self.assertIn("Press News", press_titles)
        self.assertIn("Active News", journal_titles)
        self.assertNotIn("Active News", press_titles)
        self.assertNotIn("Press News", journal_titles)


# ---------------------------------------------------------------------------
# Runner: Issue + not-in-any-issue sub-sitemaps
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class IssueSitemapTests(SitemapScenario, SitemapChecks, TestCase):
    """Issue sub-sitemaps: only canonical published articles; each article in
    exactly one issue; orphans collected in 'Not in any issue'."""

    TEMPLATE = "common/issue_sitemap.xml"

    def _issue_ctx(self, issue):
        return build_issue_sitemap_context(issue, self.journal_normal)

    def _no_issue_ctx(self):
        return build_issue_sitemap_context(None, self.journal_normal)

    def test_issue_battery(self):
        self.assert_sitemap(
            self._issue_ctx(self.issue_regular),
            names=[
                self.journal_normal.name,
                self.issue_regular.non_pretty_issue_identifier,
            ],
            level="issue",
            template=self.TEMPLATE,
            schema_kind="urlset",
            keys=[
                "issue",
                "journal",
                "article_entries",
                "parent_sitemap",
                "page_title",
                "h1",
                "sitemap_level",
            ],
        )

    def test_no_issue_battery(self):
        self.assert_sitemap(
            self._no_issue_ctx(),
            names=[self.journal_normal.name, "Not in any issue"],
            level="not-in-any-issue",
            template=self.TEMPLATE,
            schema_kind="urlset",
        )

    def test_published_article_present(self):
        self.assertIn(
            self.article_published.url, self._urls(self._issue_ctx(self.issue_regular))
        )

    def test_unpublished_article_excluded(self):
        self.assertNotIn(
            self.article_unpublished.url,
            self._urls(self._issue_ctx(self.issue_regular)),
        )

    def test_future_article_excluded(self):
        self.assertNotIn(
            self.article_future.url, self._urls(self._issue_ctx(self.issue_regular))
        )

    def test_multi_issue_article_only_in_canonical(self):
        canonical = self._urls(self._issue_ctx(self.issue_regular))
        other = self._urls(self._issue_ctx(self.issue_regular_b))
        self.assertIn(self.article_published.url, canonical)
        self.assertNotIn(self.article_published.url, other)

    def test_no_issue_contains_orphan(self):
        self.assertIn(self.article_orphan.url, self._urls(self._no_issue_ctx()))

    def test_unpublished_article_absent_from_no_issue(self):
        # "Nowhere" means truly nowhere — not the issue and not no-issue.
        self.assertNotIn(self.article_unpublished.url, self._urls(self._no_issue_ctx()))

    def test_lastmod_is_date_published(self):
        for entry in self._issue_ctx(self.issue_regular)["article_entries"]:
            if entry["url"] == self.article_published.url:
                self.assertEqual(
                    entry["lastmod"], self.article_published.date_published.isoformat()
                )
                return
        self.fail("published article entry not found")

    def test_collection_only_article_in_no_issue(self):
        # A collection is not a regular issue, so an article only in a
        # collection routes to "Not in any issue".
        self.assertIn(
            self.article_collection_only.url, self._urls(self._no_issue_ctx())
        )

    def test_regular_and_collection_article_not_in_no_issue(self):
        # article_published is in a regular issue and a collection — it stays in
        # its canonical regular issue, never in "Not in any issue".
        self.assertNotIn(self.article_published.url, self._urls(self._no_issue_ctx()))

    def test_primary_issue_collection_falls_back_to_first_regular(self):
        # primary_issue points at a collection (non-regular), so canonicalisation
        # falls back to the first regular issue (issue_regular).
        self.assertIn(
            self.article_primary_collection.url,
            self._urls(self._issue_ctx(self.issue_regular)),
        )
        self.assertNotIn(
            self.article_primary_collection.url, self._urls(self._no_issue_ctx())
        )


# ---------------------------------------------------------------------------
# Canonical issue selection: the footer and generation must file each article
# under the same single issue (or both under "not in any issue").
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="domain")
class CanonicalIssueTests(TestCase):
    """The footer canonical issue must match where generation files the article."""

    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        cls.issue_type, _ = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal,
            code="issue",
            defaults={"pretty_name": "Issue", "custom_plural": "Issues"},
        )
        cls.author = helpers.create_author(cls.journal)
        cls.section, _ = submission_models.Section.objects.get_or_create(
            journal=cls.journal, name="Test Section"
        )

        now = timezone.now()
        past = now - timezone.timedelta(days=30)
        future = now + timezone.timedelta(days=30)

        cls.issue_a = cls.make_issue("Issue A", volume=1, number=1, date=past, order=1)
        cls.issue_b = cls.make_issue("Issue B", volume=1, number=2, date=past, order=2)
        cls.issue_future = cls.make_issue(
            "Future Issue", volume=2, number=1, date=future, order=1
        )
        # Two issues sharing order and date: the pk tie-break must pick the
        # lower pk.  Created together so tie_low.pk < tie_high.pk.
        cls.issue_tie_low = cls.make_issue(
            "Tie Low", volume=3, number=1, date=past, order=5
        )
        cls.issue_tie_high = cls.make_issue(
            "Tie High", volume=3, number=2, date=past, order=5
        )

        # 1. primary_issue is a published regular issue the article belongs to.
        cls.article_primary_member = cls.make_article("Primary Member")
        cls.issue_a.articles.add(cls.article_primary_member)
        cls.issue_b.articles.add(cls.article_primary_member)
        cls.set_primary(cls.article_primary_member, cls.issue_a)

        # 2. primary_issue is a regular issue the article does NOT belong to.
        cls.article_primary_nonmember = cls.make_article("Primary Non-member")
        cls.issue_a.articles.add(cls.article_primary_nonmember)
        cls.set_primary(cls.article_primary_nonmember, cls.issue_b)

        # 3. primary_issue is a future-dated (unpublished) regular issue.
        cls.article_future_primary = cls.make_article("Future Primary")
        cls.issue_a.articles.add(cls.article_future_primary)
        cls.issue_future.articles.add(cls.article_future_primary)
        cls.set_primary(cls.article_future_primary, cls.issue_future)

        # 4. Two candidate issues tie on (order, date); lower pk wins.
        cls.article_tie = cls.make_article("Tie Break")
        cls.issue_tie_low.articles.add(cls.article_tie)
        cls.issue_tie_high.articles.add(cls.article_tie)

        # 5. Only regular issue is future-dated: no canonical issue at all.
        cls.article_future_only = cls.make_article("Future Only")
        cls.issue_future.articles.add(cls.article_future_only)

        cls.all_issues = [
            cls.issue_a,
            cls.issue_b,
            cls.issue_future,
            cls.issue_tie_low,
            cls.issue_tie_high,
        ]
        # (label, article, expected canonical issue or None)
        cls.matrix = [
            ("primary member", cls.article_primary_member, cls.issue_a),
            ("primary non-member", cls.article_primary_nonmember, cls.issue_a),
            ("future-dated primary", cls.article_future_primary, cls.issue_a),
            ("order/date tie -> lower pk", cls.article_tie, cls.issue_tie_low),
            ("future-only issue", cls.article_future_only, None),
        ]

    @classmethod
    def make_issue(cls, title, volume, number, date, order):
        return journal_models.Issue.objects.create(
            journal=cls.journal,
            volume=volume,
            issue=number,
            issue_title=title,
            issue_type=cls.issue_type,
            date=date,
            order=order,
        )

    @classmethod
    def make_article(cls, title):
        return submission_models.Article.objects.create(
            journal=cls.journal,
            owner=cls.author,
            title=title,
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )

    @classmethod
    def set_primary(cls, article, issue):
        article.primary_issue = issue
        article.save()

    def test_canonical_issue_agrees_with_generation(self):
        for label, article, expected in self.matrix:
            canonical = _canonical_issue(article)
            with self.subTest(case=label):
                self.assertEqual(
                    canonical,
                    expected,
                    "footer canonical issue diverged from the expected issue",
                )
                # The footer's canonical issue and the issue generation files
                # the article under must be the same single issue.
                for issue in self.all_issues:
                    filed_here = article in list(_canonical_articles_for_issue(issue))
                    self.assertEqual(
                        filed_here,
                        issue == canonical,
                        "article is filed under an issue that is not its footer "
                        "canonical issue (or vice versa)",
                    )

    def test_future_only_article_falls_into_not_in_any_issue(self):
        self.assertIsNone(_canonical_issue(self.article_future_only))
        self.assertIn(
            self.article_future_only,
            list(_articles_not_in_any_regular_issue(self.journal)),
            "an article whose only regular issue is future-dated vanished from "
            "every issue sitemap instead of landing in 'not in any issue'",
        )


# ---------------------------------------------------------------------------
# Runner: Subject + not-in-any-subject sub-sitemaps
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class SubjectSitemapTests(SitemapScenario, SitemapChecks, TestCase):
    """Subject sub-sitemaps: only canonical published preprints; each preprint
    in exactly one subject (alphabetically-first); orphans in 'Not in any
    subject'."""

    TEMPLATE = "common/subject_sitemap.xml"

    def _subject_ctx(self, subject):
        return build_subject_sitemap_context(subject, self.repo_live)

    def _no_subject_ctx(self):
        return build_subject_sitemap_context(None, self.repo_live)

    def test_subject_battery(self):
        self.assert_sitemap(
            self._subject_ctx(self.subject),
            names=[self.subject.name, self.repo_live.name],
            level="subject",
            template=self.TEMPLATE,
            schema_kind="urlset",
            keys=[
                "subject",
                "repo",
                "preprint_entries",
                "parent_sitemap",
                "page_title",
                "h1",
                "sitemap_level",
            ],
        )

    def test_no_subject_battery(self):
        self.assert_sitemap(
            self._no_subject_ctx(),
            names=[self.repo_live.name, "Not in any subject"],
            level="not-in-any-subject",
            template=self.TEMPLATE,
            schema_kind="urlset",
        )

    def test_published_preprint_present(self):
        self.assertIn(
            self.preprint_with_subject.url, self._urls(self._subject_ctx(self.subject))
        )

    def test_unpublished_preprint_excluded(self):
        self.assertNotIn(
            self.preprint_unpublished.url, self._urls(self._subject_ctx(self.subject))
        )

    def test_multi_subject_only_in_alphabetical_first(self):
        first = self._urls(self._subject_ctx(self.subject_alpha))
        other = self._urls(self._subject_ctx(self.subject_zeta))
        self.assertIn(self.preprint_multi.url, first)
        self.assertNotIn(self.preprint_multi.url, other)

    def test_no_subject_contains_orphan(self):
        self.assertIn(self.preprint_orphan.url, self._urls(self._no_subject_ctx()))

    def test_unpublished_preprint_absent_from_no_subject(self):
        # "Nowhere" means truly nowhere — not the subject and not no-subject.
        self.assertNotIn(
            self.preprint_unpublished.url, self._urls(self._no_subject_ctx())
        )

    def test_lastmod_is_date_published(self):
        for entry in self._subject_ctx(self.subject)["preprint_entries"]:
            if entry["url"] == self.preprint_with_subject.url:
                self.assertEqual(
                    entry["lastmod"],
                    self.preprint_with_subject.date_published.isoformat(),
                )
                return
        self.fail("preprint entry not found")


# ---------------------------------------------------------------------------
# Focused unit tests for the pure helpers the runners rely on.
# ---------------------------------------------------------------------------


class SuffixedNameTests(TestCase):
    """_suffixed_name appends a disambiguation suffix only on a name clash."""

    def test_adds_suffix_when_clash(self):
        self.assertEqual(
            _suffixed_name("Clash Name", {"Clash Name"}, "[journal]"),
            "Clash Name [journal]",
        )

    def test_unchanged_when_no_clash(self):
        self.assertEqual(
            _suffixed_name("My Journal", {"Other Name"}, "[journal]"), "My Journal"
        )


class DisambiguateLabelsByDateTests(TestCase):
    """_disambiguate_labels_by_date resolves clashing labels with progressively
    finer date suffixes, falling back to numbered suffixes."""

    @staticmethod
    def _entries(*pairs):
        from datetime import date

        return [{"title": title, "date": date(*ymd)} for title, ymd in pairs]

    def test_no_clash(self):
        entries = self._entries(("Alpha", (2020, 1, 1)), ("Beta", (2020, 2, 1)))
        _disambiguate_labels_by_date(entries)
        self.assertEqual([e["title"] for e in entries], ["Alpha", "Beta"])

    def test_year_sufficient(self):
        entries = self._entries(("News", (2020, 1, 1)), ("News", (2021, 6, 1)))
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [2020]", titles)
        self.assertIn("News [2021]", titles)

    def test_month_needed(self):
        entries = self._entries(("News", (2020, 1, 1)), ("News", (2020, 6, 1)))
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [Jan 2020]", titles)
        self.assertIn("News [Jun 2020]", titles)

    def test_sequential_fallback(self):
        entries = self._entries(("News", (2020, 1, 1)), ("News", (2020, 1, 1)))
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [#1]", titles)
        self.assertIn("News [#2]", titles)

    def test_case_insensitive(self):
        entries = self._entries(
            ("My Article", (2020, 1, 1)), ("my article", (2021, 3, 15))
        )
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("My Article [2020]", titles)
        self.assertIn("my article [2021]", titles)

    def test_day_needed(self):
        # Same month and year, different day → [DD Mon YYYY].
        entries = self._entries(("News", (2020, 1, 1)), ("News", (2020, 1, 15)))
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [01 Jan 2020]", titles)
        self.assertIn("News [15 Jan 2020]", titles)

    def test_none_date_falls_to_numbered(self):
        # A clashing entry with no date (e.g. a canonical link colliding with a
        # CMS page) forces the whole group onto numbered suffixes.
        from datetime import date

        entries = [
            {"title": "News", "date": None},
            {"title": "News", "date": date(2020, 1, 1)},
        ]
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [#1]", titles)
        self.assertIn("News [#2]", titles)


class PlainLabelTests(TestCase):
    """_plain_label converts HTML titles to plain text for the XML context."""

    def test_strips_html_tags(self):
        self.assertEqual(_plain_label("<em>italics</em>"), "italics")

    def test_decodes_amp_entity(self):
        self.assertEqual(_plain_label("A &amp; B"), "A & B")

    def test_strips_tags_and_decodes_entities(self):
        self.assertEqual(_plain_label("<em>Test &amp; thing</em>"), "Test & thing")

    def test_decodes_lt_gt_entities(self):
        self.assertEqual(_plain_label("A &lt;em&gt; B"), "A <em> B")

    def test_decodes_quot_and_apos(self):
        self.assertEqual(
            _plain_label("say &quot;hello&quot; &amp; &apos;hi&apos;"),
            "say \"hello\" & 'hi'",
        )

    def test_handles_none(self):
        self.assertEqual(_plain_label(None), "")

    def test_handles_empty_string(self):
        self.assertEqual(_plain_label(""), "")

    def test_plain_text_unchanged(self):
        self.assertEqual(_plain_label("Normal title"), "Normal title")


# ---------------------------------------------------------------------------
# XML escaping — adversarial titles (chars not present in the shared fixture).
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class XmlEscapingTests(SitemapScenario, SitemapChecks, TestCase):
    """Special characters in labels must produce well-formed, single-encoded XML."""

    NS = {"j": "https://janeway.systems"}

    def _loc_labels(self, template, ctx):
        from lxml import etree

        xml_str = render_to_string(template, ctx)
        root = etree.fromstring(xml_str.encode("utf-8"))
        labels = [el.text or "" for el in root.findall(".//j:loc_label", self.NS)]
        return labels, xml_str

    def test_news_ampersand_single_encoded(self):
        from datetime import datetime, timezone as dt_tz

        ctx = {
            "page_title": "News",
            "h1": "News",
            "sitemap_level": "press-news",
            "parent_sitemap": {"loc": "http://example.com/sitemap.xml", "label": "P"},
            "owner": self.press,
            "news_items": [
                {
                    "url": "http://example.com/news/1/",
                    "posted": datetime(2024, 1, 1, tzinfo=dt_tz.utc),
                    "title": "Cats & Dogs",
                }
            ],
        }
        labels, xml_str = self._loc_labels("common/news_sitemap.xml", ctx)
        self.assertNotIn("&amp;amp;", xml_str)
        self.assertIn("Cats & Dogs", labels)

    def test_article_html_is_plain_text(self):
        ctx = build_issue_sitemap_context(self.issue_regular, self.journal_normal)
        ctx["article_entries"][0]["title"] = _plain_label("<em>Test &amp; Article</em>")
        labels, xml_str = self._loc_labels("common/issue_sitemap.xml", ctx)
        self.assertNotIn("&amp;amp;", xml_str)
        self.assertNotIn("&lt;em&gt;", xml_str)
        self.assertIn("Test & Article", labels)

    def test_pages_special_chars_well_formed(self):
        ctx = {
            "page_title": "Pages",
            "h1": "Pages",
            "sitemap_level": "press-pages",
            "parent_sitemap": {"loc": "http://example.com/sitemap.xml", "label": "P"},
            "links": [("http://example.com/about/", 'About "Us" & <More>', None)],
        }
        labels, _xml = self._loc_labels("common/pages_sitemap.xml", ctx)
        self.assertIn('About "Us" & <More>', labels)

    def test_issue_label_ampersand_escaped(self):
        """An '&' in an issue title is XML-escaped in the journal siteindex
        (regression for the xmllint xmlParseEntityRef failure)."""
        from lxml import etree

        issue = journal_models.Issue.objects.create(
            journal=self.journal_normal,
            volume="5",
            issue="5",
            issue_title="Sound & Vision",
            issue_type=self.issue_type,
            date=timezone.now(),
        )
        article = submission_models.Article.objects.create(
            journal=self.journal_normal,
            owner=self.author,
            title="Amp Issue Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=self.section,
        )
        issue.articles.add(article)
        article.primary_issue = issue
        article.save()
        ctx = build_journal_index_context(self.journal_normal)
        xml_str = render_to_string("common/level2_sitemap.xml", ctx)
        etree.fromstring(xml_str.encode("utf-8"))  # raw '&' would raise
        self.assertIn("Sound &amp; Vision", xml_str)
        self.assertNotIn("Sound & Vision", xml_str)


# ---------------------------------------------------------------------------
# XSLT accessibility: clashing links get unique accessible names (WCAG 2.4.4).
# ---------------------------------------------------------------------------


class SitemapXsltTests(TestCase):
    """The stylesheet gives each list link a contextual accessible name via
    aria-labelledby, so two links with identical visible text but different
    destinations are distinguishable in a screen reader's list of links."""

    def test_clashing_links_unique_accessible_names(self):
        from lxml import etree

        xslt_path = os.path.join(
            settings.BASE_DIR, "static", "common", "xslt", "sitemap.xsl"
        )
        transform = etree.XSLT(etree.parse(xslt_path))
        siteindex = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
            ' xmlns:janeway="https://janeway.systems">'
            "<janeway:page_title>Sitemap - Repeated Name</janeway:page_title>"
            "<janeway:h1>Sitemap - Repeated Name</janeway:h1>"
            "<janeway:sitemap_level>journal</janeway:sitemap_level>"
            "<janeway:higher_sitemap>"
            "<janeway:loc>http://localhost/sitemap.xml</janeway:loc>"
            "<janeway:loc_label>Repeated Name</janeway:loc_label>"
            "</janeway:higher_sitemap>"
            "<sitemap><loc>http://localhost/TST/news_sitemap.xml</loc>"
            "<janeway:loc_label>Repeated Name</janeway:loc_label>"
            "<janeway:group>news</janeway:group></sitemap>"
            "</sitemapindex>"
        )
        root = transform(etree.fromstring(siteindex.encode("utf-8"))).getroot()
        by_id = {
            el.get("id"): "".join(el.itertext()).strip()
            for el in root.iter()
            if el.get("id")
        }

        def accessible_name(anchor):
            labelledby = anchor.get("aria-labelledby")
            if labelledby:
                return " ".join(by_id.get(i, "") for i in labelledby.split())
            return "".join(anchor.itertext()).strip()

        anchors = [a for a in root.iter() if etree.QName(a).localname == "a"]
        repeated = [
            accessible_name(a)
            for a in anchors
            if "".join(a.itertext()).strip() == "Repeated Name"
        ]
        # Both clashing links must be present and end up with distinct
        # accessible names (guard against a vacuous pass).
        self.assertGreaterEqual(len(repeated), 2, repeated)
        self.assertEqual(len(repeated), len(set(repeated)), repeated)


# ---------------------------------------------------------------------------
# Footer page_sitemap_url tag: maps the current page to its most specific
# sitemap. Walks the shared fixture.
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="path")
class PageSitemapURLTagTests(SitemapScenario, TestCase):
    """page_sitemap_url(context, view_name, obj) → the sitemap URL for the
    current page."""

    def _request(self, *, press=None, journal=None, repository=None):
        req = helpers.Request()
        req.press = press or self.press
        req.journal = journal
        req.repository = repository
        return req

    def _call(self, request, view_name, obj=None):
        from core.templatetags.sitemap_tags import page_sitemap_url

        return page_sitemap_url({"request": request}, view_name, obj)

    # --- press ---
    def test_press_home_returns_press_sitemap(self):
        url = self._call(self._request(), "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.press.site_url(), url)

    def test_press_news_item_returns_press_news_sitemap(self):
        url = self._call(self._request(), "core_news_item")
        self.assertTrue(url.endswith("/news_sitemap.xml"))

    def test_press_cms_page_returns_press_pages_sitemap(self):
        url = self._call(self._request(), "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))

    # --- journal ---
    def test_journal_home_returns_journal_sitemap(self):
        url = self._call(self._request(journal=self.journal_normal), "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.journal_normal.site_url(), url)

    def test_journal_news_item_returns_journal_news_sitemap(self):
        url = self._call(self._request(journal=self.journal_normal), "core_news_item")
        self.assertTrue(url.endswith("/news_sitemap.xml"))
        self.assertIn(self.journal_normal.site_url(), url)

    def test_journal_cms_page_returns_journal_pages_sitemap(self):
        url = self._call(self._request(journal=self.journal_normal), "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))
        self.assertIn(self.journal_normal.site_url(), url)

    def test_article_in_issue_returns_issue_sitemap(self):
        url = self._call(
            self._request(journal=self.journal_normal),
            "article_view",
            self.article_published,
        )
        self.assertIn(str(self.issue_regular.pk), url)
        self.assertTrue(url.endswith("_sitemap.xml"))

    def test_article_not_in_issue_returns_no_issue_sitemap(self):
        url = self._call(
            self._request(journal=self.journal_normal),
            "article_view",
            self.article_orphan,
        )
        self.assertIn("no_issue_sitemap", url)

    def test_article_without_primary_issue_uses_first_issue(self):
        # article_in_c is in issue_regular_c with no primary_issue, so the footer
        # resolves to that (first/only) regular issue.
        url = self._call(
            self._request(journal=self.journal_normal),
            "article_view",
            self.article_in_c,
        )
        self.assertIn(str(self.issue_regular_c.pk), url)
        self.assertTrue(url.endswith("_sitemap.xml"))

    def test_issue_listing_returns_journal_pages_sitemap(self):
        url = self._call(self._request(journal=self.journal_normal), "journal_issues")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))

    # --- repository ---
    def test_repo_home_returns_repo_sitemap(self):
        url = self._call(self._request(repository=self.repo_live), "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.repo_live.site_url(), url)

    def test_repo_cms_page_returns_repo_pages_sitemap(self):
        url = self._call(self._request(repository=self.repo_live), "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))

    def test_preprint_with_subject_returns_subject_sitemap(self):
        url = self._call(
            self._request(repository=self.repo_live),
            "repository_preprint",
            self.preprint_with_subject,
        )
        self.assertIn(str(self.subject.pk), url)
        self.assertTrue(url.endswith("_sitemap.xml"))

    def test_preprint_no_subject_returns_no_subject_sitemap(self):
        url = self._call(
            self._request(repository=self.repo_live),
            "repository_preprint",
            self.preprint_orphan,
        )
        self.assertIn("no_subject_sitemap", url)

    def test_preprint_multi_subject_links_to_first_alphabetical(self):
        url = self._call(
            self._request(repository=self.repo_live),
            "repository_preprint",
            self.preprint_multi,
        )
        self.assertIn(str(self.subject_alpha.pk), url)
        self.assertNotIn(str(self.subject_zeta.pk), url)

    def test_missing_request_returns_empty_string(self):
        from core.templatetags.sitemap_tags import page_sitemap_url

        self.assertEqual(page_sitemap_url({}, "website_index"), "")


# ---------------------------------------------------------------------------
# Preprint page footer: a full-page render must link the subject sub-sitemap
# that lists the preprint.
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="domain")
class SitemapPreprintFooterTests(TestCase):
    """A preprint page's footer must link to its subject sub-sitemap."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.manager = helpers.create_user("sitemap_pp_mgr@example.com")
        cls.author = helpers.create_user("sitemap_pp_author@example.com")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.manager], []
        )
        cls.preprint = helpers.create_preprint(
            cls.repository, cls.author, cls.subject, title="Footer Preprint"
        )
        cls.preprint.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.now() - timezone.timedelta(hours=1)
        cls.preprint.save()
        cls.preprint.make_new_version(cls.preprint.submission_file)

    def setUp(self):
        clear_script_prefix()

    @override_settings(INSTALLATION_BASE_THEME="material")
    def test_preprint_footer_links_to_subject_sitemap(self):
        response = self.client.get(
            reverse("repository_preprint", kwargs={"preprint_id": self.preprint.pk}),
            data={"theme": "material"},
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 200)
        subject_path = reverse(
            "repository_sitemap", kwargs={"subject_id": self.subject.pk}
        )
        self.assertContains(response, subject_path)


# ---------------------------------------------------------------------------
# generate_sitemaps command: orchestration, filters and write-gating.
# All write_* functions are patched so nothing touches disk; the test asserts
# which objects each writer is invoked for.
# ---------------------------------------------------------------------------


class GenerateSitemapsCommandTests(SitemapScenario, TestCase):
    """The management command writes the right sub-sitemaps for the right
    objects, honouring is_remote, the per-site write gates and the
    --site_type / --codes filters."""

    WRITERS = (
        "write_press_sitemap",
        "write_pages_sitemap",
        "write_news_sitemap",
        "write_journal_sitemap",
        "write_issue_sitemap",
        "write_not_in_any_issue_sitemap",
        "write_repository_sitemap",
        "write_subject_sitemap",
        "write_not_in_any_subject_sitemap",
    )

    def setUp(self):
        self.mocks = {}
        for name in self.WRITERS:
            patcher = mock.patch(f"utils.logic.{name}")
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def _written(self, writer):
        """First positional arg of each call to `writer`."""
        return [call.args[0] for call in self.mocks[writer].call_args_list]

    def test_press_sitemap_written(self):
        call_command("generate_sitemaps")
        self.assertEqual(self.mocks["write_press_sitemap"].call_count, 1)

    def test_press_news_written_when_active(self):
        call_command("generate_sitemaps")
        self.assertIn(self.press, self._written("write_news_sitemap"))

    def test_remote_journal_skipped_hosted_written(self):
        call_command("generate_sitemaps")
        written = self._written("write_journal_sitemap")
        self.assertIn(self.journal_normal, written)
        self.assertNotIn(self.journal_remote, written)

    def test_hidden_journal_still_written(self):
        call_command("generate_sitemaps")
        self.assertIn(self.journal_hidden, self._written("write_journal_sitemap"))

    def test_codes_filter_limits_to_named_journal(self):
        call_command("generate_sitemaps", codes=["TST"])
        written = self._written("write_journal_sitemap")
        self.assertIn(self.journal_normal, written)  # code TST
        self.assertNotIn(self.journal_no_news, written)  # code TSA

    def test_site_type_journals_skips_repositories(self):
        call_command("generate_sitemaps", site_type="journals")
        self.assertEqual(self.mocks["write_repository_sitemap"].call_count, 0)
        self.assertTrue(self._written("write_journal_sitemap"))

    def test_site_type_repositories_skips_journals(self):
        call_command("generate_sitemaps", site_type="repositories")
        self.assertEqual(self.mocks["write_journal_sitemap"].call_count, 0)
        self.assertIn(self.repo_live, self._written("write_repository_sitemap"))

    def test_repo_with_no_published_preprints_writes_nothing(self):
        call_command("generate_sitemaps")
        written = self._written("write_repository_sitemap")
        self.assertIn(self.repo_live, written)
        self.assertNotIn(self.repo_not_live, written)

    def test_issue_and_orphan_writers_called(self):
        call_command("generate_sitemaps")
        self.assertIn(self.issue_regular, self._written("write_issue_sitemap"))
        self.assertIn(
            self.journal_normal, self._written("write_not_in_any_issue_sitemap")
        )

    def test_subject_and_orphan_writers_called(self):
        call_command("generate_sitemaps")
        self.assertIn(self.subject_alpha, self._written("write_subject_sitemap"))
        self.assertIn(self.repo_live, self._written("write_not_in_any_subject_sitemap"))


# ---------------------------------------------------------------------------
# Serving sitemap files over HTTP: missing files 404 (never 500), and a
# repository host never serves the press news file.
# ---------------------------------------------------------------------------


@override_settings(URL_CONFIG="domain")
class SitemapServingTests(TestCase):
    """A missing press/repository sub-sitemap file must 404, not 500 or leak."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.manager = helpers.create_user("sitemap_regress_mgr@example.com")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.manager], []
        )

    def setUp(self):
        clear_script_prefix()

    @mock.patch("core.files.serve_sitemap_file", side_effect=FileNotFoundError)
    def test_press_index_sitemap_missing_file_returns_404(self, _serve):
        response = self.client.get(
            reverse("website_sitemap"),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch("core.files.serve_sitemap_file", side_effect=FileNotFoundError)
    def test_press_pages_sitemap_missing_file_returns_404(self, _serve):
        response = self.client.get(
            reverse("press_pages_sitemap"),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch("core.files.serve_sitemap_file", side_effect=FileNotFoundError)
    def test_repository_pages_sitemap_missing_file_returns_404(self, _serve):
        response = self.client.get(
            reverse("repository_pages_sitemap"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch("core.files.serve_sitemap_file", return_value=HttpResponse())
    def test_repository_news_request_does_not_serve_press_news_file(self, serve):
        # A repository has no news sitemap: the request must 404 rather than
        # fall through and stream the press-level news_sitemap.xml file.
        response = self.client.get(
            reverse("press_news_sitemap"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 404)
        serve.assert_not_called()


# ---------------------------------------------------------------------------
# Accessibility lastmod depends on a data file — fail loudly if it moves.
# ---------------------------------------------------------------------------


class AccessibilityDataFileTests(TestCase):
    """The Accessibility canonical link's lastmod is the mtime of
    a11y/conformance_data.json. This guards that dependency."""

    def test_conformance_data_file_exists(self):
        path = os.path.join(settings.BASE_DIR, "a11y", "conformance_data.json")
        self.assertTrue(
            os.path.isfile(path),
            f"Sitemap accessibility lastmod depends on {path}, which is missing. "
            f"If the file moved, update logic._accessibility_lastmod() and this test.",
        )
        # The dependency resolves to a real mtime, not the None fallback.
        self.assertIsNotNone(logic._accessibility_lastmod())
