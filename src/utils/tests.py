__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import codecs
import io
import json
import os
from unittest import expectedFailure

from bs4 import BeautifulSoup

from django.apps import apps
from django.conf import settings
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.utils import timezone, translation
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.template.engine import Engine
from django.template.loader import render_to_string

import mock
from utils import (
    merge_settings,
    models,
    oidc,
    template_override_middleware,
    logic,
    migration_utils,
)
from utils.orcid import (
    get_orcid_record_details,
    build_redirect_uri,
    encode_state,
    decode_state,
)

from utils import install
from utils.transactional_emails import *
from utils.forms import (
    FakeModelForm,
    KeywordModelForm,
    plain_text_validator,
)
from utils.logic import (
    generate_sitemap,
    build_press_index_context,
    build_journal_index_context,
    build_repo_index_context,
    build_news_sitemap_context,
    build_issue_sitemap_context,
    build_subject_sitemap_context,
    _suffixed_name,
    _disambiguate_labels_by_date,
)
from utils.testing import helpers
from utils.testing.context_managers import janeway_setting_override
from utils.shared import clear_cache
from utils.notify_plugins import notify_email
from utils.management.commands import check_mailgun_stat

from cms import models as cms_models
from journal import (
    models as journal_models,
    logic as journal_logic,
    forms as journal_forms,
)
from press import models as press_models
from repository import models as repo_models
from review import models as review_models
from submission import models as submission_models
from core import (
    email as core_email,
    models as core_models,
)
from copyediting import models as copyediting_models


def setUpModule():
    install.update_settings(management_command=False)
    install.update_emails(management_command=False)
    install.update_xsl_files(management_command=False)


class UtilsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["reviewer", "editor", "author", "section-editor"])

        cls.journal_one = journal_models.Journal.objects.get(
            code="TST", domain="testserver"
        )

        cls.regular_user = helpers.create_regular_user()
        cls.second_user = helpers.create_second_user(cls.journal_one)
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.editor_two = helpers.create_editor(
            cls.journal_one, email="editor2@example.com"
        )
        cls.section_editor = helpers.create_section_editor(cls.journal_one)
        cls.author = helpers.create_author(cls.journal_one)
        cls.coauthor = helpers.create_author(
            cls.journal_one, email="coauthor@example.org"
        )
        cls.copyeditor = helpers.create_copyeditor(cls.journal_one)

        setting_handler.save_setting(
            "general",
            "submission_access_request_contact",
            cls.journal_one,
            cls.editor.email,
        )

        cls.submitted_article = helpers.create_article(cls.journal_one)
        cls.author.snapshot_as_author(cls.submitted_article)
        cls.submitted_article.correspondence_author = cls.author
        cls.coauthor.snapshot_as_author(cls.submitted_article)

        cls.review_form = review_models.ReviewForm.objects.create(
            name="A Form", intro="i", thanks="t", journal=cls.journal_one
        )

        cls.article_under_review = helpers.create_article(
            journal=cls.journal_one,
            title="A Test Article",
            owner=cls.author,
            correspondence_author=cls.author,
            abstract="An abstract",
            stage=submission_models.STAGE_UNDER_REVIEW,
        )
        cls.author.snapshot_as_author(cls.article_under_review)
        cls.coauthor.snapshot_as_author(cls.article_under_review)

        cls.review_assignment = review_models.ReviewAssignment.objects.create(
            article=cls.article_under_review,
            reviewer=cls.second_user,
            editor=cls.editor,
            date_due=timezone.now(),
            form=cls.review_form,
        )

        cls.access_request = helpers.create_access_request(
            cls.journal_one,
            cls.author,
            "author",
        )

        cls.request = helpers.Request()
        cls.request.journal = cls.journal_one
        cls.request.press = cls.journal_one.press
        cls.request.site_type = cls.journal_one
        cls.request.user = cls.editor
        cls.request.model_content_type = ContentType.objects.get_for_model(
            cls.request.journal
        )

        cls.test_message = "This message is a test for outgoing email, nothing else."

        cls.base_kwargs = {
            "request": cls.request,
            "user_message_content": cls.test_message,
            "skip": False,
        }

        # Setup issues for sitemap testing
        cls.issue_type, created = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal_one,
            code="issue",
            defaults={"pretty_name": "Issue", "custom_plural": "Issues"},
        )
        cls.issue_one, created = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_one,
            volume="1",
            issue="1",
            issue_title="V 1 I 1",
            issue_type=cls.issue_type,
        )
        cls.section, create = submission_models.Section.objects.get_or_create(
            journal=cls.journal_one,
            name="Test Section",
        )
        cls.article_one, created = submission_models.Article.objects.get_or_create(
            journal=cls.journal_one,
            owner=cls.author,
            title="This is a test article",
            abstract="This is an abstract",
            stage=submission_models.STAGE_PUBLISHED,
            section=cls.section,
            defaults={
                "date_accepted": timezone.now(),
                "date_published": timezone.now(),
            },
        )
        cls.issue_one.articles.add(cls.article_one)

    # Helper function for email subjects
    def get_default_email_subject(self, setting_name, journal=None):
        journal = journal or self.journal_one
        group = "email_subject"
        subject = setting_handler.get_email_subject_setting(
            group, setting_name, journal
        )
        if subject != setting_name:
            # The test shouldn't pass unless the setting or a default was retrieved.
            # The name serves as a backup in production but shouldn't be let through in testing.
            return subject


class SitemapTests(UtilsTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.news_item = helpers.create_news_item(
            ContentType.objects.get_for_model(cls.press),
            cls.press.pk,
        )
        cls.news_item.start_display = timezone.now() - timezone.timedelta(days=1)
        cls.news_item.posted = timezone.now() - timezone.timedelta(days=1)
        cls.news_item.save()

        # Repository fixture for subject/no-subject sitemap tests.
        cls.repo_manager_user = helpers.create_user("sm_repo_mgr@example.com")
        cls.repository, cls.repo_subject = helpers.create_repository(
            cls.press, [cls.repo_manager_user], []
        )

    @override_settings(URL_CONFIG="path")
    def test_press_sitemap_generation(self):
        file = io.StringIO()
        generate_sitemap(
            file=file,
            press=self.press,
        )
        soup = BeautifulSoup(file.getvalue(), "xml")
        self.assertEqual(
            soup.select("sitemap_name")[0].get_text(strip=True),
            "Press",
        )
        # The pages_sitemap.xml child is referenced with the owner-prefixed
        # label "{owner.name} pages" (so labels stay unique under WCAG 2.4.4
        # when listed alongside child journals/repos).
        all_labels = [el.get_text(strip=True) for el in soup.select("loc_label")]
        self.assertIn(f"{self.press.name} pages", all_labels)

    @override_settings(URL_CONFIG="path")
    def test_journal_sitemap_generation(self):
        file = io.StringIO()
        generate_sitemap(
            file=file,
            journal=self.journal_one,
        )
        soup = BeautifulSoup(file.getvalue(), "xml")
        self.assertEqual(
            soup.select("sitemap_name")[0].get_text(strip=True),
            "Journal One",
        )
        self.assertEqual(
            soup.select("higher_sitemap loc_label")[0].get_text(strip=True),
            "Press",
        )
        # pages_sitemap.xml child is the first entry, labelled with the
        # owner-prefixed "{journal.name} pages".
        all_labels = [el.get_text(strip=True) for el in soup.select("loc_label")]
        self.assertIn(f"{self.journal_one.name} pages", all_labels)
        self.assertEqual(
            soup.select("sitemap > loc_label")[0].get_text(strip=True),
            f"{self.journal_one.name} pages",
        )

    @override_settings(URL_CONFIG="path")
    def test_issue_sitemap_generation(self):
        file = io.StringIO()
        generate_sitemap(
            file=file,
            issue=self.issue_one,
        )
        soup = BeautifulSoup(file.getvalue(), "xml")
        self.assertIn(
            self.issue_one.non_pretty_issue_identifier,
            soup.select("sitemap_name")[0].get_text(strip=True),
        )
        self.assertEqual(
            soup.select("higher_sitemap loc_label")[0].get_text(strip=True),
            "Journal One",
        )
        self.assertEqual(
            soup.select("urlset url loc")[0].get_text(strip=True),
            self.article_one.url,
        )
        self.assertEqual(
            soup.select("urlset url loc_label")[0].get_text(strip=True),
            self.article_one.title,
        )

    # -------------------------------------------------------------------
    # Context builder structural tests
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_press_context_builder_returns_required_keys(self):
        """build_press_index_context returns a dict with all required keys."""
        ctx = build_press_index_context(self.press)
        self.assertIn("press", ctx)
        self.assertIn("child_sitemaps", ctx)
        self.assertIn("page_title", ctx)
        self.assertIn("h1", ctx)

    @override_settings(URL_CONFIG="path")
    def test_press_context_builder_page_title_and_h1(self):
        """Press context page_title and h1 both equal 'Sitemap - {press.name}'."""
        ctx = build_press_index_context(self.press)
        expected = f"Sitemap - {self.press.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_press_context_builder_static_links_type(self):
        """Press pages context links is a list of 3-tuples (url, label, lastmod)."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.press)
        self.assertIsInstance(ctx["links"], list)
        for item in ctx["links"]:
            self.assertEqual(len(item), 3)

    @override_settings(URL_CONFIG="path")
    def test_journal_context_builder_returns_required_keys(self):
        """build_journal_index_context returns a dict with all required keys."""
        ctx = build_journal_index_context(self.journal_one)
        for key in (
            "journal",
            "child_sitemaps",
            "parent_sitemap",
            "page_title",
            "h1",
            "site_name",
        ):
            self.assertIn(key, ctx)

    @override_settings(URL_CONFIG="path")
    def test_journal_context_builder_page_title_and_h1(self):
        """Journal context page_title and h1 both equal 'Sitemap - {journal.name}'."""
        ctx = build_journal_index_context(self.journal_one)
        expected = f"Sitemap - {self.journal_one.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_issue_context_builder_returns_required_keys(self):
        """build_issue_sitemap_context returns a dict with all required keys."""
        ctx = build_issue_sitemap_context(self.issue_one, self.journal_one)
        for key in (
            "issue",
            "journal",
            "article_entries",
            "parent_sitemap",
            "page_title",
            "h1",
        ):
            self.assertIn(key, ctx)

    @override_settings(URL_CONFIG="path")
    def test_issue_context_builder_page_title_contains_identifier(self):
        """Issue context page_title includes the issue identifier and journal name."""
        ctx = build_issue_sitemap_context(self.issue_one, self.journal_one)
        self.assertIn(self.issue_one.non_pretty_issue_identifier, ctx["page_title"])
        self.assertIn(self.journal_one.name, ctx["page_title"])

    @override_settings(URL_CONFIG="path")
    def test_no_issue_context_builder_page_title(self):
        """'Not in any issue' context has correct page_title and h1."""
        ctx = build_issue_sitemap_context(None, self.journal_one)
        expected = f"Sitemap - Not in any issue, {self.journal_one.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_news_context_builder_press_page_title(self):
        """Press news context has 'News sitemap - {press.name}' title."""
        ctx = build_news_sitemap_context(self.press)
        expected = f"News sitemap - {self.press.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_news_context_builder_journal_page_title(self):
        """Journal news context has 'News sitemap - {journal.name}' title."""
        ctx = build_news_sitemap_context(self.journal_one)
        expected = f"News sitemap - {self.journal_one.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_news_context_builder_returns_required_keys(self):
        """build_news_sitemap_context returns a dict with all required keys."""
        ctx = build_news_sitemap_context(self.press)
        for key in ("owner", "news_items", "parent_sitemap", "page_title", "h1"):
            self.assertIn(key, ctx)

    def test_write_news_sitemap_for_press_uses_root_path(self):
        """write_news_sitemap for a press writes to the sitemaps root, not a subdirectory.

        The press news sitemap is served from /news_sitemap.xml (path_parts=[]).
        A previous bug used [press.code] as path_parts, writing to /{press.code}/news_sitemap.xml
        which the view could not find.
        """
        from unittest.mock import patch, mock_open
        from utils.logic import write_news_sitemap

        with (
            patch(
                "utils.logic.get_sitemap_path", return_value="/tmp/news_sitemap.xml"
            ) as mock_gsp,
            patch("utils.logic.render_to_string", return_value="<xml/>"),
            patch("builtins.open", mock_open()),
        ):
            write_news_sitemap(self.press)

        mock_gsp.assert_called_once_with(path_parts=[], file_name="news_sitemap.xml")

    # -------------------------------------------------------------------
    # static_links: alphabetical order, no URL duplicates
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_press_static_links_are_alphabetical(self):
        """Press pages links are sorted alphabetically by label (case-insensitive)."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.press)
        labels = [label for _url, label, _lastmod in ctx["links"]]
        self.assertEqual(labels, sorted(labels, key=str.lower))

    @override_settings(URL_CONFIG="path")
    def test_press_static_links_no_url_duplicates(self):
        """Press pages links contain no duplicate URLs."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.press)
        urls = [url for url, _label, _lastmod in ctx["links"]]
        self.assertEqual(len(urls), len(set(urls)))

    @override_settings(URL_CONFIG="path")
    def test_journal_static_links_are_alphabetical(self):
        """Journal pages links are sorted alphabetically by label (case-insensitive)."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.journal_one)
        labels = [label for _url, label, _lastmod in ctx["links"]]
        self.assertEqual(labels, sorted(labels, key=str.lower))

    @override_settings(URL_CONFIG="path")
    def test_journal_static_links_no_url_duplicates(self):
        """Journal pages links contain no duplicate URLs."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.journal_one)
        urls = [url for url, _label, _lastmod in ctx["links"]]
        self.assertEqual(len(urls), len(set(urls)))

    # -------------------------------------------------------------------
    # News items: -posted ordering
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_news_context_builder_news_items_ordered_by_posted_descending(self):
        """News context news_items are ordered by posted descending (newest first)."""
        # Create two journal news items with different posted dates.
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        older = helpers.create_news_item(journal_ct, self.journal_one.pk)
        older.start_display = timezone.now() - timezone.timedelta(days=5)
        older.posted = timezone.now() - timezone.timedelta(days=5)
        older.save()

        newer = helpers.create_news_item(journal_ct, self.journal_one.pk)
        newer.start_display = timezone.now() - timezone.timedelta(days=1)
        newer.posted = timezone.now() - timezone.timedelta(days=1)
        newer.save()

        try:
            ctx = build_news_sitemap_context(self.journal_one)
            posted_dates = [item["posted"] for item in ctx["news_items"]]
            self.assertEqual(posted_dates, sorted(posted_dates, reverse=True))
        finally:
            older.delete()
            newer.delete()

    # -------------------------------------------------------------------
    # News listing canonical: gated by active_news_items only.
    # nav_news only controls whether the default nav link is rendered;
    # the /news/ URL is always served by the comms.news_list view, so
    # whenever active news exists the canonical link must be in the
    # pages sitemap regardless of nav_news.
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_news_listing_excluded_from_static_links_when_no_news_items(self):
        """/news/ is absent from the journal pages sitemap when there are no
        active news items."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.journal_one)
        urls = [url for url, _label, _lastmod in ctx["links"]]
        self.assertFalse(any("/news/" in u for u in urls))

    @override_settings(URL_CONFIG="path")
    def test_news_listing_included_in_static_links_when_news_items_exist(self):
        """/news/ is present in the journal pages sitemap when the journal has
        at least one active news item."""
        from utils.logic import build_pages_sitemap_context

        # Django caches ContentType lookups process-wide; that cache survives
        # the test DB being recreated, so get_for_model can hand back IDs from
        # a previous DB.  Clear it before we trust it.
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        news = helpers.create_news_item(journal_ct, self.journal_one.pk)
        news.start_display = (timezone.now() - timezone.timedelta(days=1)).date()
        news.posted = timezone.now() - timezone.timedelta(days=1)
        news.save()
        try:
            ctx = build_pages_sitemap_context(self.journal_one)
            urls = [url for url, _label, _lastmod in ctx["links"]]
            self.assertTrue(any("/news/" in u for u in urls))
        finally:
            news.delete()

    @override_settings(URL_CONFIG="path")
    def test_news_listing_included_when_nav_news_false_but_active_news_exist(
        self,
    ):
        """nav_news=False must not hide /news/ from the sitemap if active news
        exists. nav_news only governs the default nav link, while /news/ is
        always served by the comms.news_list view."""
        from utils.logic import build_pages_sitemap_context

        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        news = helpers.create_news_item(journal_ct, self.journal_one.pk)
        news.start_display = (timezone.now() - timezone.timedelta(days=1)).date()
        news.posted = timezone.now() - timezone.timedelta(days=1)
        news.save()
        original_nav_news = self.journal_one.nav_news
        self.journal_one.nav_news = False
        self.journal_one.save()
        try:
            ctx = build_pages_sitemap_context(self.journal_one)
            urls = [url for url, _label, _lastmod in ctx["links"]]
            self.assertTrue(any("/news/" in u for u in urls))
        finally:
            self.journal_one.nav_news = original_nav_news
            self.journal_one.save()
            news.delete()

    # -------------------------------------------------------------------
    # News sub-sitemap context: active_news_items display-window gating.
    # ActiveNewsItemManager filters with
    #   (start_display__lte=now() | start_display=None)
    #   & (end_display__gte=now() | end_display=None)
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_news_sub_sitemap_excludes_future_dated_items(self):
        """A NewsItem whose start_display is in the future is filtered out
        of build_news_sitemap_context."""
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        future = helpers.create_news_item(
            journal_ct,
            self.journal_one.pk,
            title="Future story",
        )
        future.start_display = (timezone.now() + timezone.timedelta(days=7)).date()
        future.save()
        try:
            ctx = build_news_sitemap_context(self.journal_one)
            titles = [item["title"] for item in ctx["news_items"]]
            self.assertNotIn("Future story", titles)
        finally:
            future.delete()

    @override_settings(URL_CONFIG="path")
    def test_news_sub_sitemap_excludes_expired_items(self):
        """A NewsItem whose end_display is in the past is filtered out of
        build_news_sitemap_context."""
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        expired = helpers.create_news_item(
            journal_ct,
            self.journal_one.pk,
            title="Expired story",
        )
        expired.start_display = (timezone.now() - timezone.timedelta(days=30)).date()
        expired.end_display = (timezone.now() - timezone.timedelta(days=1)).date()
        expired.save()
        try:
            ctx = build_news_sitemap_context(self.journal_one)
            titles = [item["title"] for item in ctx["news_items"]]
            self.assertNotIn("Expired story", titles)
        finally:
            expired.delete()

    @override_settings(URL_CONFIG="path")
    def test_news_sub_sitemap_includes_items_at_window_boundaries(self):
        """start_display==today and end_display==today are inclusive — the
        manager uses __lte / __gte."""
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        today = timezone.now().date()
        start_today = helpers.create_news_item(
            journal_ct,
            self.journal_one.pk,
            title="Starts today",
        )
        start_today.start_display = today
        start_today.save()
        end_today = helpers.create_news_item(
            journal_ct,
            self.journal_one.pk,
            title="Ends today",
        )
        end_today.start_display = today - timezone.timedelta(days=10)
        end_today.end_display = today
        end_today.save()
        try:
            ctx = build_news_sitemap_context(self.journal_one)
            titles = [item["title"] for item in ctx["news_items"]]
            self.assertIn("Starts today", titles)
            self.assertIn("Ends today", titles)
        finally:
            start_today.delete()
            end_today.delete()

    @override_settings(URL_CONFIG="path")
    def test_news_sub_sitemap_includes_items_with_null_display_window(self):
        """start_display=None and end_display=None match the second branch
        of each Q clause and so are always considered active."""
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        open_window = helpers.create_news_item(
            journal_ct,
            self.journal_one.pk,
            title="No window",
        )
        open_window.start_display = None
        open_window.end_display = None
        open_window.save()
        try:
            ctx = build_news_sitemap_context(self.journal_one)
            titles = [item["title"] for item in ctx["news_items"]]
            self.assertIn("No window", titles)
        finally:
            open_window.delete()

    # -------------------------------------------------------------------
    # Siteindex gating: news sub-sitemap entry only appears when active
    # news items exist on the owner.
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_press_index_includes_news_when_active_news_exist(self):
        """build_press_index_context references the news sub-sitemap when
        the press has at least one active news item (fixture provides
        cls.news_item with start_display in the past)."""
        ctx = build_press_index_context(self.press)
        groups = [c["group"] for c in ctx["child_sitemaps"]]
        self.assertIn("news", groups)

    @override_settings(URL_CONFIG="path")
    def test_press_index_excludes_news_when_no_active_news(self):
        """build_press_index_context does not reference the news sub-sitemap
        when the press has no active news items."""
        self.news_item.delete()
        ctx = build_press_index_context(self.press)
        groups = [c["group"] for c in ctx["child_sitemaps"]]
        self.assertNotIn("news", groups)

    @override_settings(URL_CONFIG="path")
    def test_journal_index_excludes_news_when_no_active_news(self):
        """build_journal_index_context does not reference the news sub-sitemap
        when the journal has no active news items."""
        ctx = build_journal_index_context(self.journal_one)
        groups = [c["group"] for c in ctx["child_sitemaps"]]
        self.assertNotIn("news", groups)

    @override_settings(URL_CONFIG="path")
    def test_journal_index_includes_news_when_active_news_exist(self):
        """build_journal_index_context references the news sub-sitemap when
        the journal has at least one active news item."""
        ContentType.objects.clear_cache()
        journal_ct = ContentType.objects.get_for_model(self.journal_one)
        news = helpers.create_news_item(journal_ct, self.journal_one.pk)
        news.start_display = (timezone.now() - timezone.timedelta(days=1)).date()
        news.save()
        try:
            ctx = build_journal_index_context(self.journal_one)
            groups = [c["group"] for c in ctx["child_sitemaps"]]
            self.assertIn("news", groups)
        finally:
            news.delete()

    # -------------------------------------------------------------------
    # generate_sitemaps command: news-write gating mirrors the index gate.
    # All write_* functions are patched so the test does not touch disk.
    # -------------------------------------------------------------------

    @mock.patch("utils.logic.write_not_in_any_subject_sitemap")
    @mock.patch("utils.logic.write_subject_sitemap")
    @mock.patch("utils.logic.write_repository_sitemap")
    @mock.patch("utils.logic.write_not_in_any_issue_sitemap")
    @mock.patch("utils.logic.write_issue_sitemap")
    @mock.patch("utils.logic.write_news_sitemap")
    @mock.patch("utils.logic.write_pages_sitemap")
    @mock.patch("utils.logic.write_journal_sitemap")
    @mock.patch("utils.logic.write_press_sitemap")
    def test_generate_sitemaps_writes_news_when_press_has_active_news(
        self,
        mock_press,
        mock_journal,
        mock_pages,
        mock_news,
        mock_issue,
        mock_not_in_issue,
        mock_repo,
        mock_subject,
        mock_not_in_subject,
    ):
        """The command invokes write_news_sitemap(press) when the press has
        active news items."""
        call_command("generate_sitemaps")
        owners = [c[0][0] for c in mock_news.call_args_list]
        self.assertIn(self.press, owners)

    @mock.patch("utils.logic.write_not_in_any_subject_sitemap")
    @mock.patch("utils.logic.write_subject_sitemap")
    @mock.patch("utils.logic.write_repository_sitemap")
    @mock.patch("utils.logic.write_not_in_any_issue_sitemap")
    @mock.patch("utils.logic.write_issue_sitemap")
    @mock.patch("utils.logic.write_news_sitemap")
    @mock.patch("utils.logic.write_pages_sitemap")
    @mock.patch("utils.logic.write_journal_sitemap")
    @mock.patch("utils.logic.write_press_sitemap")
    def test_generate_sitemaps_skips_news_when_press_has_no_active_news(
        self,
        mock_press,
        mock_journal,
        mock_pages,
        mock_news,
        mock_issue,
        mock_not_in_issue,
        mock_repo,
        mock_subject,
        mock_not_in_subject,
    ):
        """The command does NOT invoke write_news_sitemap(press) when the
        press has no active news items."""
        self.news_item.delete()
        call_command("generate_sitemaps")
        owners = [c[0][0] for c in mock_news.call_args_list]
        self.assertNotIn(self.press, owners)

    # -------------------------------------------------------------------
    # "Not in any issue" sub-sitemap
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_issue_listed_in_journal_context_when_articles_exist(self):
        """Journal context child_sitemaps includes 'Not in any issue' when orphan articles exist."""
        # article_one is already in issue_one via cls.issue_one.articles.add(cls.article_one).
        # Create a published article NOT in any issue.
        orphan = submission_models.Article.objects.create(
            journal=self.journal_one,
            owner=self.author,
            title="Orphan Article",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
        )
        try:
            self.assertTrue(self.journal_one.published_articles_not_in_issues.exists())
            ctx = build_journal_index_context(self.journal_one)
            child_labels = [child["label"] for child in ctx["child_sitemaps"]]
            self.assertIn("Not in any issue", child_labels)
        finally:
            orphan.delete()

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_issue_absent_from_journal_context_when_no_orphan_articles(self):
        """Journal context child_sitemaps omits 'Not in any issue' when no orphan articles exist."""
        # Ensure no orphan articles for journal_two (which has no articles at all).
        self.assertFalse(self.journal_two.published_articles_not_in_issues.exists())
        ctx = build_journal_index_context(self.journal_two)
        child_labels = [child["label"] for child in ctx["child_sitemaps"]]
        self.assertNotIn("Not in any issue", child_labels)

    @override_settings(URL_CONFIG="path")
    def test_empty_issue_excluded_from_journal_child_sitemaps(self):
        """An issue with no articles is not listed in the journal sitemap's child_sitemaps."""
        empty_issue = helpers.create_issue(self.journal_one, vol=99, number=99)
        self.assertFalse(empty_issue.get_sorted_articles().exists())
        try:
            ctx = build_journal_index_context(self.journal_one)
            child_locs = [child["loc"] for child in ctx["child_sitemaps"]]
            issue_url = f"{self.journal_one.site_url()}{reverse('journal_sitemap', kwargs={'issue_id': empty_issue.pk})}"
            self.assertNotIn(issue_url, child_locs)
        finally:
            empty_issue.delete()

    @override_settings(URL_CONFIG="path")
    def test_issue_with_articles_included_in_journal_child_sitemaps(self):
        """An issue with articles is listed in the journal sitemap's child_sitemaps."""
        ctx = build_journal_index_context(self.journal_one)
        child_locs = [child["loc"] for child in ctx["child_sitemaps"]]
        issue_url = f"{self.journal_one.site_url()}{reverse('journal_sitemap', kwargs={'issue_id': self.issue_one.pk})}"
        self.assertIn(issue_url, child_locs)

    @override_settings(URL_CONFIG="path")
    def test_no_issue_context_builder_uses_published_articles_not_in_issues(self):
        """'Not in any issue' context article_entries contains the journal's orphan articles."""
        ctx = build_issue_sitemap_context(None, self.journal_one)
        expected_pks = set(
            self.journal_one.published_articles_not_in_issues.values_list(
                "pk", flat=True
            )
        )
        actual_pks = {entry["pk"] for entry in ctx["article_entries"]}
        self.assertEqual(actual_pks, expected_pks)

    # -------------------------------------------------------------------
    # "Not in any subject" sub-sitemap
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_no_subject_context_builder_page_title(self):
        """'Not in any subject' context has correct page_title and h1."""
        ctx = build_subject_sitemap_context(None, self.repository)
        expected = f"Sitemap - Not in any subject, {self.repository.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_no_subject_context_builder_returns_required_keys(self):
        """build_subject_sitemap_context(None, repo) returns a dict with all required keys."""
        ctx = build_subject_sitemap_context(None, self.repository)
        for key in (
            "subject",
            "repo",
            "preprint_entries",
            "parent_sitemap",
            "page_title",
            "h1",
        ):
            self.assertIn(key, ctx)

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_subject_listed_in_repo_context_when_preprints_exist(self):
        """Repo context child_sitemaps includes 'Not in any subject' when orphan preprints exist."""
        # Create a published preprint with no subject.
        author = helpers.create_user("orphan_author@example.com")
        orphan = repo_models.Preprint.objects.create(
            repository=self.repository,
            owner=author,
            stage=repo_models.STAGE_PREPRINT_PUBLISHED,
            title="Orphan Preprint",
            abstract="No subject here.",
            comments_editor="",
            date_submitted=timezone.now(),
            date_published=timezone.now() - timezone.timedelta(hours=1),
        )
        # No subject added — so subject is empty.
        try:
            self.assertTrue(logic._preprints_without_subject(self.repository).exists())
            ctx = build_repo_index_context(self.repository)
            child_labels = [child["label"] for child in ctx["child_sitemaps"]]
            self.assertIn("Not in any subject", child_labels)
        finally:
            orphan.delete()

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_subject_absent_from_repo_context_when_no_orphan_preprints(self):
        """Repo context child_sitemaps omits 'Not in any subject' when no orphan preprints."""
        # No preprints were created for this repository, so preprints_without_subject is empty.
        # This test verifies the omission when the queryset is empty.
        self.assertFalse(logic._preprints_without_subject(self.repository).exists())
        ctx = build_repo_index_context(self.repository)
        child_labels = [child["label"] for child in ctx["child_sitemaps"]]
        self.assertNotIn("Not in any subject", child_labels)

    @override_settings(URL_CONFIG="path")
    def test_empty_subject_excluded_from_repo_child_sitemaps(self):
        """A subject with no published preprints is not listed in the repo sitemap's child_sitemaps."""
        empty_subject, _ = repo_models.Subject.objects.get_or_create(
            repository=self.repository,
            name="Empty Subject",
            slug="empty-subject",
            defaults={"enabled": True},
        )
        self.assertFalse(empty_subject.published_preprints().exists())
        try:
            ctx = build_repo_index_context(self.repository)
            child_locs = [child["loc"] for child in ctx["child_sitemaps"]]
            subject_url = f"{self.repository.site_url()}{reverse('repository_sitemap', kwargs={'subject_id': empty_subject.pk})}"
            self.assertNotIn(subject_url, child_locs)
        finally:
            empty_subject.delete()

    @override_settings(URL_CONFIG="path")
    def test_subject_with_preprints_included_in_repo_child_sitemaps(self):
        """A subject with published preprints is listed in the repo sitemap's child_sitemaps."""
        author = helpers.create_user("subject_preprint_author@example.com")
        preprint = repo_models.Preprint.objects.create(
            repository=self.repository,
            owner=author,
            stage=repo_models.STAGE_PREPRINT_PUBLISHED,
            title="Subject Preprint",
            abstract="Has a subject.",
            comments_editor="",
            date_submitted=timezone.now(),
            date_published=timezone.now() - timezone.timedelta(hours=1),
        )
        preprint.subject.add(self.repo_subject)
        try:
            ctx = build_repo_index_context(self.repository)
            child_locs = [child["loc"] for child in ctx["child_sitemaps"]]
            subject_url = f"{self.repository.site_url()}{reverse('repository_sitemap', kwargs={'subject_id': self.repo_subject.pk})}"
            self.assertIn(subject_url, child_locs)
        finally:
            preprint.delete()

    # -------------------------------------------------------------------
    # Rendered XML contains <janeway:page_title> and <janeway:h1>
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_press_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered press sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        file = io.StringIO()
        generate_sitemap(file=file, press=self.press)
        soup = BeautifulSoup(file.getvalue(), "xml")
        expected = f"Sitemap - {self.press.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_journal_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered journal sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        file = io.StringIO()
        generate_sitemap(file=file, journal=self.journal_one)
        soup = BeautifulSoup(file.getvalue(), "xml")
        expected = f"Sitemap - {self.journal_one.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_issue_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered issue sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        file = io.StringIO()
        generate_sitemap(file=file, issue=self.issue_one)
        soup = BeautifulSoup(file.getvalue(), "xml")
        expected_fragment = self.issue_one.non_pretty_issue_identifier
        self.assertIn(
            expected_fragment,
            soup.select("page_title")[0].get_text(strip=True),
        )
        self.assertIn(
            expected_fragment,
            soup.select("h1")[0].get_text(strip=True),
        )

    @override_settings(URL_CONFIG="path")
    def test_repo_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered repository sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        file = io.StringIO()
        generate_sitemap(file=file, repository=self.repository)
        soup = BeautifulSoup(file.getvalue(), "xml")
        expected = f"Sitemap - {self.repository.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_subject_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered subject sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        file = io.StringIO()
        generate_sitemap(file=file, subject=self.repo_subject)
        soup = BeautifulSoup(file.getvalue(), "xml")
        expected = f"Sitemap - {self.repo_subject.name}, {self.repository.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_press_news_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered press news sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        ctx = build_news_sitemap_context(self.press)
        xml = render_to_string("common/news_sitemap.xml", ctx)
        soup = BeautifulSoup(xml, "xml")
        expected = f"News sitemap - {self.press.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_journal_news_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered journal news sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        ctx = build_news_sitemap_context(self.journal_one)
        xml = render_to_string("common/news_sitemap.xml", ctx)
        soup = BeautifulSoup(xml, "xml")
        expected = f"News sitemap - {self.journal_one.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_issue_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered 'not in any issue' sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        ctx = build_issue_sitemap_context(None, self.journal_one)
        xml = render_to_string("common/issue_sitemap.xml", ctx)
        soup = BeautifulSoup(xml, "xml")
        expected = f"Sitemap - Not in any issue, {self.journal_one.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    @override_settings(URL_CONFIG="path")
    def test_not_in_any_subject_sitemap_xml_contains_page_title_and_h1(self):
        """Rendered 'not in any subject' sitemap XML contains <janeway:page_title> and <janeway:h1>."""
        ctx = build_subject_sitemap_context(None, self.repository)
        xml = render_to_string("common/subject_sitemap.xml", ctx)
        soup = BeautifulSoup(xml, "xml")
        expected = f"Sitemap - Not in any subject, {self.repository.name}"
        self.assertEqual(soup.select("page_title")[0].get_text(strip=True), expected)
        self.assertEqual(soup.select("h1")[0].get_text(strip=True), expected)

    # -------------------------------------------------------------------
    # sitemap_level key in context dicts
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_press_context(self):
        """build_press_index_context returns sitemap_level='press'."""
        ctx = build_press_index_context(self.press)
        self.assertEqual(ctx["sitemap_level"], "press")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_journal_context(self):
        """build_journal_index_context returns sitemap_level='journal'."""
        ctx = build_journal_index_context(self.journal_one)
        self.assertEqual(ctx["sitemap_level"], "journal")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_issue_context(self):
        """build_issue_sitemap_context returns sitemap_level='issue' for a real issue."""
        ctx = build_issue_sitemap_context(self.issue_one, self.journal_one)
        self.assertEqual(ctx["sitemap_level"], "issue")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_not_in_issue_context(self):
        """build_issue_sitemap_context returns sitemap_level='not-in-any-issue' for None."""
        ctx = build_issue_sitemap_context(None, self.journal_one)
        self.assertEqual(ctx["sitemap_level"], "not-in-any-issue")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_press_news_context(self):
        """build_news_sitemap_context returns sitemap_level='press-news' for press owner."""
        ctx = build_news_sitemap_context(self.press)
        self.assertEqual(ctx["sitemap_level"], "press-news")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_journal_news_context(self):
        """build_news_sitemap_context returns sitemap_level='journal-news' for journal owner."""
        ctx = build_news_sitemap_context(self.journal_one)
        self.assertEqual(ctx["sitemap_level"], "journal-news")

    # -------------------------------------------------------------------
    # Name-clash disambiguation helpers
    # -------------------------------------------------------------------

    def test_suffixed_name_adds_suffix_when_clash(self):
        """_suffixed_name appends suffix when name is in clash_names."""
        result = _suffixed_name("Clash Name", {"Clash Name"}, "[journal]")
        self.assertEqual(result, "Clash Name [journal]")

    def test_suffixed_name_unchanged_when_no_clash(self):
        """_suffixed_name returns name unchanged when name is not in clash_names."""
        result = _suffixed_name("My Journal", {"Other Name"}, "[journal]")
        self.assertEqual(result, "My Journal")

    @override_settings(URL_CONFIG="path")
    def test_name_clash_adds_journal_suffix_in_press_child_sitemaps(self):
        """When press name matches a journal name, child sitemap label gets [journal] suffix.

        Press.name is a plain DB field (no caching), so changing it in-memory is
        enough for _build_clash_names to detect the clash without touching the DB.
        """
        original_press_name = self.press.name
        self.press.name = self.journal_one.name
        try:
            ctx = build_press_index_context(self.press)
            journal_labels = [
                child["label"]
                for child in ctx["child_sitemaps"]
                if child["group"] == "journals"
            ]
            self.assertTrue(
                any(
                    f"{self.journal_one.name} [journal]" == label
                    for label in journal_labels
                ),
                f"Expected '[journal]' suffix in labels: {journal_labels}",
            )
        finally:
            self.press.name = original_press_name

    @override_settings(URL_CONFIG="path")
    def test_no_clash_no_suffix_in_press_child_sitemaps(self):
        """When journal names do not clash, no suffix is added to child sitemap labels."""
        ctx = build_press_index_context(self.press)
        journal_labels = [
            child["label"]
            for child in ctx["child_sitemaps"]
            if child["group"] == "journals"
        ]
        self.assertFalse(
            any("[journal]" in label for label in journal_labels),
            f"Unexpected '[journal]' suffix in labels: {journal_labels}",
        )

    # -------------------------------------------------------------------
    # _disambiguate_labels_by_date unit tests
    # -------------------------------------------------------------------

    def test_disambiguate_labels_by_date_no_clash(self):
        """Entries with distinct titles are returned unchanged."""
        from datetime import date

        entries = [
            {"title": "Alpha", "date": date(2020, 1, 1)},
            {"title": "Beta", "date": date(2020, 2, 1)},
        ]
        _disambiguate_labels_by_date(entries)
        self.assertEqual(entries[0]["title"], "Alpha")
        self.assertEqual(entries[1]["title"], "Beta")

    def test_disambiguate_labels_by_date_year_sufficient(self):
        """Clashing titles are resolved with [year] when years differ."""
        from datetime import date

        entries = [
            {"title": "News", "date": date(2020, 1, 1)},
            {"title": "News", "date": date(2021, 6, 1)},
        ]
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [2020]", titles)
        self.assertIn("News [2021]", titles)

    def test_disambiguate_labels_by_date_month_needed(self):
        """When years clash, [Mon YYYY] is used."""
        from datetime import date

        entries = [
            {"title": "News", "date": date(2020, 1, 1)},
            {"title": "News", "date": date(2020, 6, 1)},
        ]
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [Jan 2020]", titles)
        self.assertIn("News [Jun 2020]", titles)

    def test_disambiguate_labels_by_date_sequential_fallback(self):
        """When even day-level dates clash, sequential [#N] suffixes are used."""
        from datetime import date

        entries = [
            {"title": "News", "date": date(2020, 1, 1)},
            {"title": "News", "date": date(2020, 1, 1)},
        ]
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("News [#1]", titles)
        self.assertIn("News [#2]", titles)

    def test_disambiguate_labels_by_date_case_insensitive(self):
        """Titles that differ only in case are treated as clashing."""
        from datetime import date

        entries = [
            {"title": "My Article", "date": date(2020, 1, 1)},
            {"title": "my article", "date": date(2021, 3, 15)},
        ]
        _disambiguate_labels_by_date(entries)
        titles = [e["title"] for e in entries]
        self.assertIn("My Article [2020]", titles)
        self.assertIn("my article [2021]", titles)

    # -------------------------------------------------------------------
    # Issue label deduplication
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_issue_labels_disambiguated_when_clashing(self):
        """Issues with identical non_pretty_issue_identifier get PK-disambiguated labels."""
        issue_two = journal_models.Issue.objects.create(
            journal=self.journal_one,
            volume=self.issue_one.volume,
            issue=self.issue_one.issue,
            issue_title=self.issue_one.issue_title,
            issue_type=self.issue_type,
            date=self.issue_one.date,
        )
        try:
            ctx = build_journal_index_context(self.journal_one)
            issue_labels = [
                child["label"]
                for child in ctx["child_sitemaps"]
                if child["group"] == "issues" and child["label"] != "Not in any issue"
            ]
            self.assertEqual(
                len(set(issue_labels)),
                len(issue_labels),
                f"Duplicate issue labels found: {issue_labels}",
            )
            for label in issue_labels:
                self.assertIn(self.issue_one.non_pretty_issue_identifier, label)
        finally:
            issue_two.delete()

    # -------------------------------------------------------------------
    # level2 XML contains janeway:group
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_level2_xml_child_sitemaps_contain_group_element(self):
        """Rendered level2 sitemap XML includes <janeway:group> on each child sitemap."""
        import io as _io

        file = _io.StringIO()
        generate_sitemap(file=file, journal=self.journal_one)
        soup = BeautifulSoup(file.getvalue(), "xml")
        child_groups = soup.select("sitemapindex > sitemap > group")
        self.assertTrue(
            len(child_groups) > 0,
            "Expected at least one <janeway:group> in child sitemaps",
        )


class SitemapRepoTests(TestCase):
    """Sitemap tests requiring a repository fixture."""

    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        cls.press = helpers.create_press()
        cls.repo_manager = helpers.create_user("repo_mgr_sitemap@example.com")
        cls.repo_author = helpers.create_user("repo_author_sitemap@example.com")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.repo_manager], []
        )

    @override_settings(URL_CONFIG="path")
    def test_repo_context_builder_returns_required_keys(self):
        """build_repo_index_context returns a dict with all required keys."""
        ctx = build_repo_index_context(self.repository)
        for key in (
            "repo",
            "child_sitemaps",
            "parent_sitemap",
            "page_title",
            "h1",
            "site_name",
        ):
            self.assertIn(key, ctx)

    @override_settings(URL_CONFIG="path")
    def test_repo_context_builder_page_title_and_h1(self):
        """Repo context page_title and h1 both equal 'Sitemap - {repo.name}'."""
        ctx = build_repo_index_context(self.repository)
        expected = f"Sitemap - {self.repository.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    @override_settings(URL_CONFIG="path")
    def test_repo_static_links_are_alphabetical(self):
        """Repo pages links are sorted alphabetically by label (case-insensitive)."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.repository)
        labels = [label for _url, label, _lastmod in ctx["links"]]
        self.assertEqual(labels, sorted(labels, key=str.lower))

    @override_settings(URL_CONFIG="path")
    def test_subject_context_builder_returns_required_keys(self):
        """build_subject_sitemap_context returns a dict with all required keys."""
        ctx = build_subject_sitemap_context(self.subject, self.repository)
        for key in (
            "subject",
            "repo",
            "preprint_entries",
            "parent_sitemap",
            "page_title",
            "h1",
        ):
            self.assertIn(key, ctx)

    @override_settings(URL_CONFIG="path")
    def test_subject_context_builder_page_title(self):
        """Subject context page_title includes subject name and repo name."""
        ctx = build_subject_sitemap_context(self.subject, self.repository)
        expected = f"Sitemap - {self.subject.name}, {self.repository.name}"
        self.assertEqual(ctx["page_title"], expected)
        self.assertEqual(ctx["h1"], expected)

    # -------------------------------------------------------------------
    # sitemap_level for repo / subject / not-in-any-subject
    # -------------------------------------------------------------------

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_repo_context(self):
        """build_repo_index_context returns sitemap_level='repository'."""
        ctx = build_repo_index_context(self.repository)
        self.assertEqual(ctx["sitemap_level"], "repository")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_subject_context(self):
        """build_subject_sitemap_context returns sitemap_level='subject' for a real subject."""
        ctx = build_subject_sitemap_context(self.subject, self.repository)
        self.assertEqual(ctx["sitemap_level"], "subject")

    @override_settings(URL_CONFIG="path")
    def test_sitemap_level_in_not_in_subject_context(self):
        """build_subject_sitemap_context returns sitemap_level='not-in-any-subject' for None."""
        ctx = build_subject_sitemap_context(None, self.repository)
        self.assertEqual(ctx["sitemap_level"], "not-in-any-subject")


class PageSitemapURLTagTests(TestCase):
    """Tests for the page_sitemap_url template tag (§5 table in the plan)."""

    @classmethod
    def setUpTestData(cls):
        call_command("load_default_settings")
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.journal_one = journal_models.Journal.objects.get(
            code="TST", domain="testserver"
        )
        cls.repo_manager = helpers.create_user("repo_mgr_tag@example.com")
        cls.repo_author = helpers.create_user("repo_author_tag@example.com")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.repo_manager], []
        )

        # Published article in an issue.
        cls.issue_type, _ = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal_one,
            code="tag_test_issue_type",
            pretty_name="Tag Test Issue Type",
            custom_plural="Tag Test Issues",
        )
        cls.issue, _ = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_one,
            volume="2",
            issue="1",
            issue_title="V 2 I 1",
            issue_type=cls.issue_type,
        )
        cls.author = helpers.create_author(cls.journal_one)
        cls.section, _ = submission_models.Section.objects.get_or_create(
            journal=cls.journal_one,
            name="Tag Test Section",
        )
        cls.article_in_issue = submission_models.Article.objects.create(
            journal=cls.journal_one,
            owner=cls.author,
            title="Article in issue (tag test)",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )
        cls.issue.articles.add(cls.article_in_issue)

        cls.article_not_in_issue = submission_models.Article.objects.create(
            journal=cls.journal_one,
            owner=cls.author,
            title="Article not in issue (tag test)",
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(hours=1),
            section=cls.section,
        )

        cls.preprint_with_subject = helpers.create_preprint(
            cls.repository, cls.repo_author, cls.subject
        )
        cls.preprint_with_subject.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint_with_subject.date_published = timezone.now() - timezone.timedelta(
            hours=1
        )
        cls.preprint_with_subject.save()

        cls.preprint_no_subject = repo_models.Preprint.objects.create(
            repository=cls.repository,
            owner=cls.repo_author,
            stage=repo_models.STAGE_PREPRINT_PUBLISHED,
            title="No Subject Preprint (tag test)",
            abstract="Abstract.",
            comments_editor="",
            date_submitted=timezone.now(),
            date_published=timezone.now() - timezone.timedelta(hours=1),
        )
        # No subject added to preprint_no_subject.

    def _make_tag_context(self, request):
        """Returns a minimal template tag context containing the request."""
        return {"request": request}

    def _press_request(self):
        """Returns a fake press-scoped request."""
        req = helpers.Request()
        req.press = self.press
        req.journal = None
        req.repository = None
        return req

    def _journal_request(self):
        """Returns a fake journal-scoped request."""
        req = helpers.Request()
        req.press = self.press
        req.journal = self.journal_one
        req.repository = None
        return req

    def _repo_request(self):
        """Returns a fake repository-scoped request."""
        req = helpers.Request()
        req.press = self.press
        req.journal = None
        req.repository = self.repository
        return req

    # Import the tag function at test time to avoid top-level circular issues.
    def _call_tag(self, context, view_name, obj=None):
        from core.templatetags.sitemap_tags import page_sitemap_url

        return page_sitemap_url(context, view_name, obj)

    # §5 table row: Press home / press CMS / press editorial / press contact
    @override_settings(URL_CONFIG="path")
    def test_press_home_returns_press_sitemap(self):
        ctx = self._make_tag_context(self._press_request())
        url = self._call_tag(ctx, "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.press.site_url(), url)

    # §5 table row: Press news item
    @override_settings(URL_CONFIG="path")
    def test_press_news_item_returns_press_news_sitemap(self):
        ctx = self._make_tag_context(self._press_request())
        url = self._call_tag(ctx, "core_news_item")
        self.assertTrue(url.endswith("/news_sitemap.xml"))
        self.assertIn(self.press.site_url(), url)

    # §5 table row: Press CMS page
    @override_settings(URL_CONFIG="path")
    def test_press_cms_page_returns_press_pages_sitemap(self):
        ctx = self._make_tag_context(self._press_request())
        url = self._call_tag(ctx, "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))
        self.assertIn(self.press.site_url(), url)

    # Journal home
    @override_settings(URL_CONFIG="path")
    def test_journal_home_returns_journal_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.journal_one.site_url(), url)

    # §5 table row: Journal news item
    @override_settings(URL_CONFIG="path")
    def test_journal_news_item_returns_journal_news_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "core_news_item")
        self.assertTrue(url.endswith("/news_sitemap.xml"))
        self.assertIn(self.journal_one.site_url(), url)

    # §5 table row: Journal CMS page
    @override_settings(URL_CONFIG="path")
    def test_journal_cms_page_returns_journal_pages_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))
        self.assertIn(self.journal_one.site_url(), url)

    # §5 table row: Article (in an issue)
    @override_settings(URL_CONFIG="path")
    def test_article_in_issue_returns_issue_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "article_view", self.article_in_issue)
        # Should be the issue sitemap URL, which includes the issue PK.
        self.assertIn(str(self.issue.pk), url)
        self.assertTrue(url.endswith("_sitemap.xml"))

    # §5 table row: Article (not in an issue)
    @override_settings(URL_CONFIG="path")
    def test_article_not_in_issue_returns_no_issue_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "article_view", self.article_not_in_issue)
        self.assertIn("no_issue_sitemap", url)

    # §5 table row: Issue listing — not home, not article/news, so → static sitemap
    @override_settings(URL_CONFIG="path")
    def test_issue_listing_returns_journal_pages_sitemap(self):
        ctx = self._make_tag_context(self._journal_request())
        url = self._call_tag(ctx, "journal_issues")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))
        self.assertIn(self.journal_one.site_url(), url)

    # §5 table row: Repository home / about / list
    @override_settings(URL_CONFIG="path")
    def test_repo_home_returns_repo_sitemap(self):
        ctx = self._make_tag_context(self._repo_request())
        url = self._call_tag(ctx, "website_index")
        self.assertTrue(url.endswith("/sitemap.xml"))
        self.assertIn(self.repository.site_url(), url)

    # §5 table row: Repository CMS page
    @override_settings(URL_CONFIG="path")
    def test_repo_cms_page_returns_repo_pages_sitemap(self):
        ctx = self._make_tag_context(self._repo_request())
        url = self._call_tag(ctx, "cms_page")
        self.assertTrue(url.endswith("/pages_sitemap.xml"))
        self.assertIn(self.repository.site_url(), url)

    # §5 table row: Preprint (with subject)
    @override_settings(URL_CONFIG="path")
    def test_preprint_with_subject_returns_subject_sitemap(self):
        ctx = self._make_tag_context(self._repo_request())
        url = self._call_tag(ctx, "repository_preprint", self.preprint_with_subject)
        self.assertIn(str(self.subject.pk), url)
        self.assertTrue(url.endswith("_sitemap.xml"))

    # §5 table row: Preprint (no subject)
    @override_settings(URL_CONFIG="path")
    def test_preprint_no_subject_returns_no_subject_sitemap(self):
        ctx = self._make_tag_context(self._repo_request())
        url = self._call_tag(ctx, "repository_preprint", self.preprint_no_subject)
        self.assertIn("no_subject_sitemap", url)

    # Preprint with multiple subjects → footer links to first-by-name subject.
    @override_settings(URL_CONFIG="path")
    def test_preprint_multi_subject_footer_links_to_first_alphabetical_subject(self):
        """When a preprint has two subjects, the footer sitemap URL points to
        the subject whose name sorts first alphabetically, not the first by pk."""
        subject_a = repo_models.Subject.objects.create(
            repository=self.repository,
            name="Aardvark Studies",
            slug="tag-aardvark",
        )
        subject_z = repo_models.Subject.objects.create(
            repository=self.repository,
            name="Zoology",
            slug="tag-zoology",
        )
        # Add both subjects; subject_z has a lower pk (created first in some
        # orderings) so without order_by("name") the wrong one could be returned.
        self.preprint_with_subject.subject.set([subject_a, subject_z])
        try:
            ctx = self._make_tag_context(self._repo_request())
            url = self._call_tag(ctx, "repository_preprint", self.preprint_with_subject)
            self.assertIn(str(subject_a.pk), url)
            self.assertNotIn(str(subject_z.pk), url)
        finally:
            self.preprint_with_subject.subject.set([self.subject])
            subject_a.delete()
            subject_z.delete()

    # Edge case: missing request in context returns empty string.
    def test_missing_request_returns_empty_string(self):
        url = self._call_tag({}, "website_index")
        self.assertEqual(url, "")


class TransactionalReviewEmailTests(UtilsTests):
    """
    These test cases cover transactional emails sent
    in the review stage.
    """

    def test_send_reviewer_withdrawl_notice(self):
        kwargs = {
            "review_assignment": self.review_assignment,
            "request": self.request,
            "user_message_content": self.test_message,
            "skip": False,
        }

        expected_recipient = self.review_assignment.reviewer.email
        subject_setting_name = "subject_review_withdrawl"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        email_data = core_email.EmailData(
            subject=subject_setting,
            body=self.test_message,
        )
        kwargs["email_data"] = email_data

        send_reviewer_withdrawl_notice(**kwargs)

        self.assertEqual(expected_recipient, mail.outbox[0].to[0])

        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_editor_unassigned_notice(self):
        expected_recipient_one = self.review_assignment.editor.email
        subject_setting_name = "subject_unassign_editor"
        subject_setting = self.get_default_email_subject(
            subject_setting_name,
            journal=self.review_assignment.article.journal,
        )
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)

        email_data = core_email.EmailData(
            subject=subject_setting,
            body=self.test_message,
        )
        send_editor_unassigned_notice(
            request=self.request,
            email_data=email_data,
            assignment=self.review_assignment,
        )

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_editor_assigned_acknowledgements(self):
        editor_assignment = helpers.create_editor_assignment(
            article=self.article_under_review,
            editor=self.editor_two,
        )
        subject_setting_name = "subject_editor_assignment"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        email_data = core_email.EmailData(
            subject=subject_setting,
            body=self.test_message,
        )

        expected_recipient_one = editor_assignment.editor.email
        kwargs = dict(**self.base_kwargs)
        kwargs["editor_assignment"] = editor_assignment
        kwargs["acknowledgment"] = True
        kwargs["email_data"] = email_data
        send_editor_assigned_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_reviewer_requested_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["review_assignment"] = self.review_assignment

        expected_recipient_one = self.review_assignment.reviewer.email
        send_reviewer_requested_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_review_assignment"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_review_complete_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["review_assignment"] = self.review_assignment

        send_review_complete_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_review_complete_reviewer_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])

        subject_setting_name = "subject_review_complete_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)

    def test_send_reviewer_accepted_or_decline_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["review_assignment"] = self.review_assignment

        # reviewer accepted
        kwargs["accepted"] = True
        send_reviewer_accepted_or_decline_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_review_accept_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])

        subject_setting_name = "subject_reviewer_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)

        # reviewer declined
        kwargs["accepted"] = False
        send_reviewer_accepted_or_decline_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[2].to[0])

        subject_setting_name = "subject_review_decline_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[2].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[3].to[0])

        subject_setting_name = "subject_reviewer_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[3].subject)

    def test_send_submission_acknowledgement(self):
        """
        Tests whether subjects are correct, nothing else.
        Testing recipients would require some cleaning up of
        test data in the setup method.
        """

        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.submitted_article

        send_submission_acknowledgement(**kwargs)

        # first email subject
        subject_setting_name = "subject_submission_acknowledgement"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email subject
        subject_setting_name = "subject_editor_new_submission"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)

    def test_send_submission_acknowledgement_uses_journal_replyto(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.submitted_article

        with janeway_setting_override(
            "general", "replyto_address", self.journal_one, "replyto@example.com"
        ):
            send_submission_acknowledgement(**kwargs)

        self.assertEqual(mail.outbox[1].reply_to, ["replyto@example.com"])

    def test_send_submission_acknowledgement_falls_back_to_noreply(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.submitted_article

        with janeway_setting_override(
            "general", "replyto_address", self.journal_one, ""
        ):
            send_submission_acknowledgement(**kwargs)

        self.assertIn(settings.DUMMY_EMAIL_DOMAIN, mail.outbox[1].reply_to[0])

    def test_send_article_decision(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.article_under_review
        expected_recipient_one = self.article_under_review.correspondence_author.email

        for i, decision in enumerate(["accept", "decline"]):  # to be added: 'undecline'
            kwargs["decision"] = decision
            subject_setting_name = f"subject_review_decision_{decision}"
            subject_setting = self.get_default_email_subject(subject_setting_name)
            email_data = core_email.EmailData(
                subject=subject_setting,
                body=self.test_message,
            )
            kwargs["email_data"] = email_data

            send_article_decision(**kwargs)

            self.assertEqual(expected_recipient_one, mail.outbox[i].to[0])

            expected_subject = "[{0}] {1}".format(
                self.journal_one.code, subject_setting
            )
            self.assertEqual(expected_subject, mail.outbox[i].subject)

    def test_send_revisions_request(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["revision"] = helpers.create_revision_request(
            article=self.article_under_review,
            editor=self.editor,
        )
        subject_setting_name = "subject_request_revisions"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        email_data = core_email.EmailData(
            subject=subject_setting,
            body=self.test_message,
        )
        kwargs["email_data"] = email_data

        send_revisions_request(**kwargs)

        expected_recipient_one = self.article_under_review.correspondence_author.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_request_revisions"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    @mock.patch("utils.render_template.get_message_content")
    def test_send_revisions_complete(self, render_template):
        render_template.return_value = self.test_message
        kwargs = dict(**self.base_kwargs)
        kwargs["revision"] = helpers.create_revision_request(
            article=self.article_under_review,
            editor=self.editor,
        )

        send_revisions_complete(**kwargs)

        expected_recipient_one = self.editor.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_revisions_complete_receipt"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_revisions_author_receipt(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["revision"] = helpers.create_revision_request(
            article=self.article_under_review,
            editor=self.editor,
        )

        send_revisions_author_receipt(**kwargs)

        expected_recipient_one = self.article_under_review.correspondence_author.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = "subject_revisions_complete_receipt"
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


class CopyeditingEmailSubjectTests(UtilsTests):
    """
    This class covers email subjects used in transactional_emails
    with the exception of review emails (covered above) and
    production and typesetting (not being actively developed)
    """

    def test_copyediting_email_subjects(self):
        for email_function, subject_setting_name in (
            (send_copyedit_assignment, "subject_copyeditor_assignment_notification"),
            (send_copyedit_updated, "subject_copyedit_updated"),
            (send_copyedit_deleted, "subject_copyedit_deleted"),
            (send_copyedit_decision, "subject_copyediting_decision"),
            (send_copyedit_author_review, "subject_copyeditor_notify_author"),
            (send_copyedit_complete, "subject_copyeditor_notify_editor"),
            (send_copyedit_ack, "subject_copyeditor_ack"),
            (send_copyedit_reopen, "subject_copyeditor_reopen_task"),
            (send_author_copyedit_complete, "subject_author_copyedit_complete"),
        ):
            subject_setting = self.get_default_email_subject(
                subject_setting_name,
                journal=self.article_under_review.journal,
            )

            email_data = core_email.EmailData(
                subject=subject_setting,
                body=self.test_message,
            )
            kwargs = dict(**self.base_kwargs)
            kwargs["email_data"] = email_data
            expected_subject = "[{0}] {1}".format(
                self.journal_one.code, subject_setting
            )
            kwargs["copyedit_assignment"] = helpers.create_copyedit_assignment(
                article=self.article_under_review,
                copyeditor=self.copyeditor,
                editor=self.editor,
            )
            kwargs["copyedit"] = kwargs["copyedit_assignment"]
            kwargs["decision"] = "test_decision"
            kwargs["article"] = self.article_under_review
            kwargs["author_review"], created = (
                copyediting_models.AuthorReview.objects.get_or_create(
                    author=self.author, assignment=kwargs["copyedit"], notified=True
                )
            )
            email_data = core_email.EmailData(
                subject=subject_setting,
                body=self.test_message,
            )
            email_function(**kwargs)
            expected_subject = "[{0}] {1}".format(
                self.journal_one.code, subject_setting
            )
            self.assertEqual(expected_subject, mail.outbox[-1].subject)


class PrepubEmailTests(UtilsTests):
    def test_send_prepub_notifications(self):
        request = self.base_kwargs["request"]
        article = self.article_under_review
        helpers.create_editor_assignment(
            article,
            self.section_editor,
            assignment_type="section-editor",
        )
        reviewer = helpers.create_peer_reviewer(self.journal_one)
        review_assignment = helpers.create_review_assignment(
            journal=self.journal_one,
            article=article,
            reviewer=reviewer,
            editor=self.editor,
        )
        review_assignment.is_complete = True
        review_assignment.date_declined = None
        review_assignment.decision = "yes"
        review_assignment.save()
        form_kwargs = {
            "email_context": {
                "article": article,
            },
            "request": request,
        }
        initial = journal_logic.get_initial_for_prepub_notifications(
            request,
            article,
        )
        form_data = {
            "form-TOTAL_FORMS": len(initial),
            "form-INITIAL_FORMS": "0",
            "form-0-to": initial[0]["to"],
            "form-0-cc": initial[0]["cc"],
            "form-0-subject": "Article Publication",
            "form-0-body": self.journal_one.get_setting("email", "author_publication"),
            "form-1-to": initial[1]["to"],
            "form-1-bcc": initial[1]["bcc"],
            "form-1-subject": "Article You Reviewed",
            "form-1-body": self.journal_one.get_setting(
                "email", "peer_reviewer_pub_notification"
            ),
        }
        formset = journal_forms.PrepubNotificationFormSet(
            form_data,
            form_kwargs=form_kwargs,
        )
        self.assertTrue(formset.is_valid())
        send_prepub_notifications(
            request=request,
            article=article,
            formset=formset,
        )
        subject_setting = self.get_default_email_subject("subject_author_publication")
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertIn(self.author.email, mail.outbox[0].to)
        self.assertIn(self.coauthor.email, mail.outbox[0].cc)
        self.assertIn(self.section_editor.email, mail.outbox[0].cc)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        subject_setting = self.get_default_email_subject(
            "subject_peer_reviewer_pub_notification"
        )
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertNotIn(self.author.email, mail.outbox[1].to)
        self.assertNotIn(self.author.email, mail.outbox[1].cc)
        self.assertNotIn(self.author.email, mail.outbox[1].bcc)
        self.assertNotIn(reviewer.email, mail.outbox[1].to)
        self.assertNotIn(reviewer.email, mail.outbox[1].cc)
        self.assertIn(self.editor.email, mail.outbox[1].to)
        self.assertIn(reviewer.email, mail.outbox[1].bcc)
        self.assertEqual(expected_subject, mail.outbox[1].subject)


class MiscEmailSubjectTests(UtilsTests):
    """
    These test cases cover transactional email subjects outside a workflow stage.
    """

    def test_send_draft_decison(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.article_under_review
        kwargs["draft"], created = review_models.DecisionDraft.objects.get_or_create(
            article=kwargs["article"],
            editor=self.editor,
            section_editor=self.section_editor,
            message_to_editor="Test Message",
        )
        send_draft_decison(**kwargs)

        subject_setting = self.get_default_email_subject("subject_draft_editor_message")
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_draft_decision_declined(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["article"] = self.article_under_review
        kwargs["draft_decision"], created = (
            review_models.DecisionDraft.objects.get_or_create(
                article=kwargs["article"],
                editor=self.editor,
                section_editor=self.section_editor,
                message_to_editor="Test Message",
            )
        )
        send_draft_decision_declined(**kwargs)

        subject_setting = self.get_default_email_subject(
            "subject_notify_se_draft_declined"
        )
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_access_request_notification(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["access_request"] = self.access_request
        access_request_notification(**kwargs)

        subject_setting = self.get_default_email_subject(
            "subject_submission_access_request_notification"
        )
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_access_request_complete(self):
        kwargs = dict(**self.base_kwargs)
        kwargs["access_request"] = self.access_request
        kwargs["decision"] = "Test Decision"
        access_request_complete(**kwargs)

        subject_setting = self.get_default_email_subject(
            "subject_submission_access_request_complete"
        )
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


class TestMergeSettings(TestCase):
    def test_recursive_merge(self):
        base = {
            "setting": "value",
            "setting_a": "value_a",
            "setting_list": ["value_a"],
            "setting_dict": {"a": "a", "b": "a"},
        }

        overrides = {
            "setting_a": "value_b",
            "setting_list": ["value_b"],
            "setting_dict": {"b": "b", "c": "c"},
            "other_setting": "value",
        }

        expected = {
            "setting": "value",
            "setting_a": "value_b",
            "setting_list": ["value_a", "value_b"],
            "setting_dict": {"a": "a", "b": "b", "c": "c"},
            "other_setting": "value",
        }
        result = merge_settings(base, overrides)

        self.assertDictEqual(expected, result)


class TestForms(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        helpers.create_journals()

        cls.journal = journal_models.Journal.objects.get(
            code="TST", domain="testserver"
        )

    def test_fake_model_form(self):
        class FakeTestForm(FakeModelForm):
            class Meta:
                model = journal_models.Journal
                exclude = tuple()

        form = FakeTestForm()

        with self.assertRaises(NotImplementedError):
            form.save()

    def test_keyword_form(self):
        class KeywordTestForm(KeywordModelForm):
            class Meta:
                model = journal_models.Journal
                fields = ("code",)
                exclude = tuple()

        expected = "Expected Keyword"
        data = {
            "keywords": "Keyword, another one, and another one,%s" % expected,
            "code": self.journal.code,
        }
        form = KeywordTestForm(data, instance=self.journal)
        valid = form.is_valid()

        journal = form.save()
        self.assertTrue(journal.keywords.filter(word=expected).exists())

    def test_keyword_form_empty_string(self):
        class KeywordTestForm(KeywordModelForm):
            class Meta:
                model = journal_models.Journal
                fields = ("keywords",)
                exclude = tuple()

        data = {"keywords": ""}
        form = KeywordTestForm(data, instance=self.journal)
        form.is_valid()
        journal = form.save()
        self.assertFalse(journal.keywords.exists())


class TestPlainTextValidator(TestCase):
    def test_plain_text_validator_valid(self):
        name_test = "Kathryn Janeway"
        ampersand_test = "Voyager & co"
        try:
            plain_text_validator(name_test)
            plain_text_validator(ampersand_test)
        except ValidationError:
            self.fail("Valid plain text input raised a ValidationError")

    def test_plain_text_validator_invalid(self):
        rogue_input = 'Borg <span onClick="alert()"> Queen'
        with self.assertRaises(ValidationError):
            plain_text_validator(rogue_input)


class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.ten_articles = {helpers.create_article(cls.journal_one) for i in range(10)}

    def test_log_entry_bulk_add_simple_entry(self):
        types = "Submission"
        pks = ",".join([str(article.pk) for article in self.ten_articles])
        description = f"Sending request for article {pks}"
        level = "Info"
        models.LogEntry.bulk_add_simple_entry(
            types,
            description,
            level,
            self.ten_articles,
        )
        log_entries = models.LogEntry.objects.filter(types="Submission").order_by(
            "-date"
        )[:10]
        articles = {entry.target for entry in log_entries}
        self.assertSetEqual(self.ten_articles, articles)


class NotifyEmail(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = mock.Mock()
        cls.request.site_type.name = "Mock request site type name"
        cls.request.FILES = None

    def test_send_email_reply_to(self):
        args = [
            "subject",
            "to@example.com",
            "html_body",
            self.journal_one,
            self.request,
        ]

        kwargs = {
            "bcc": "bcc@example.com",
            "cc": "cc@example.com",
            "replyto": "replyto@example.com",
        }

        with mock.patch(
            "utils.notify_plugins.notify_email.EmailMultiAlternatives"
        ) as msg:
            notify_email.send_email(*args, **kwargs)
            self.assertIn(kwargs["replyto"], msg.call_args.kwargs["reply_to"])


class TestOIDC(TestCase):
    @override_settings(
        OIDC_OP_TOKEN_ENDPOINT="test.janeway.systems/token",
        OIDC_OP_USER_ENDPOINT="test.janeway.systems/user",
        OIDC_OP_JWKS_ENDPOINT="test.janeway.systems/jwks",
        OIDC_RP_CLIENT_ID="test",
        OIDC_RP_CLIENT_SECRET="test",
        OIDC_RP_SIGN_ALGO="RS256",
    )
    def test_create_user(self):
        oidc_auth_backend = oidc.JanewayOIDCAB()
        claims = {
            "given_name": "Andy",
            "family_name": "Byers",
            "email": "andy@janeway.systems",
        }
        user = oidc_auth_backend.create_user(claims=claims)

        self.assertEqual(
            user.email,
            "andy@janeway.systems",
        )
        self.assertEqual(
            user.username,
            "andy@janeway.systems",
        )

    @override_settings(
        OIDC_OP_TOKEN_ENDPOINT="test.janeway.systems/token",
        OIDC_OP_USER_ENDPOINT="test.janeway.systems/user",
        OIDC_OP_JWKS_ENDPOINT="test.janeway.systems/jwks",
        OIDC_RP_CLIENT_ID="test",
        OIDC_RP_CLIENT_SECRET="test",
        OIDC_RP_SIGN_ALGO="RS256",
    )
    def test_update_user(self):
        user = core_models.Account.objects.create(
            first_name="Andy",
            last_name="Byers",
            email="andy@janeway.systems",
        )
        oidc_auth_backend = oidc.JanewayOIDCAB()
        claims = {
            "given_name": "Andrew",
            "family_name": "Byers",
            "email": "andy@janeway.systems",
        }
        oidc_user = oidc_auth_backend.update_user(user, claims=claims)
        self.assertEqual(
            oidc_user.first_name,
            "Andrew",
        )


class TestThemeMiddleware(TestCase):
    def setUp(self):
        self.journal_one, self.journal_two = helpers.create_journals()

    def test_unalatered_themes(self):
        engine = Engine()
        loader = template_override_middleware.Loader(engine)
        dirs = loader.get_theme_dirs()
        self.assertEqual(
            dirs,
            [
                os.path.join(
                    settings.BASE_DIR,
                    "themes",
                    settings.INSTALLATION_BASE_THEME,
                    "templates",
                )
            ],
        )

    def test_journal_dirs_with_theme(self):
        setting_handler.save_setting(
            "general",
            "journal_theme",
            self.journal_one,
            "LCARS",
        )
        # the middleware heavily caches these settings so we need to clear it.
        clear_cache()

        request = helpers.Request()
        request.journal = self.journal_one
        with helpers.request_context(request):
            engine = Engine()
            loader = template_override_middleware.Loader(engine)
            dirs = loader.get_theme_dirs()

            # in this instance INSTALLATION_BASE_THEME and the base_theme setting will match so only one
            # will appear
            self.assertEqual(
                dirs,
                [
                    os.path.join(settings.BASE_DIR, "themes", "LCARS", "templates"),
                    os.path.join(settings.BASE_DIR, "themes", "OLH", "templates"),
                ],
            )

    def test_journal_dirs_with_theme_and_base_theme(self):
        setting_handler.save_setting(
            "general",
            "journal_theme",
            self.journal_one,
            "LCARS",
        )
        setting_handler.save_setting(
            "general",
            "journal_base_theme",
            self.journal_one,
            "material",
        )
        # the middleware heavily caches these settings so we need to clear it.
        clear_cache()

        request = helpers.Request()
        request.journal = self.journal_one
        with helpers.request_context(request):
            engine = Engine()
            loader = template_override_middleware.Loader(engine)
            dirs = loader.get_theme_dirs()

            # in this instance all three themes should be in the dirs as they are all
            # different.
            self.assertEqual(
                dirs,
                [
                    os.path.join(settings.BASE_DIR, "themes", "LCARS", "templates"),
                    os.path.join(settings.BASE_DIR, "themes", "material", "templates"),
                    os.path.join(settings.BASE_DIR, "themes", "OLH", "templates"),
                ],
            )


class PlainLabelTests(SitemapTests):
    """Unit tests for _plain_label — the function that converts HTML titles to plain text
    before they enter the XML sitemap context.

    Inherits from SitemapTests so that self.press, self.journal_one,
    self.issue_one and self.repository fixtures are available for the
    rendering and schema-validation tests below.
    """

    def setUp(self):
        from utils.logic import _plain_label

        self.plain_label = _plain_label

    def test_strips_html_tags(self):
        self.assertEqual(self.plain_label("<em>italics</em>"), "italics")

    def test_decodes_amp_entity(self):
        self.assertEqual(self.plain_label("A &amp; B"), "A & B")

    def test_strips_tags_and_decodes_entities(self):
        """HTML stored in DB as <em>text &amp; more</em> produces clean plain text."""
        self.assertEqual(self.plain_label("<em>Test &amp; thing</em>"), "Test & thing")

    def test_decodes_lt_gt_entities(self):
        self.assertEqual(self.plain_label("A &lt;em&gt; B"), "A <em> B")

    def test_decodes_quot_and_apos(self):
        self.assertEqual(
            self.plain_label("say &quot;hello&quot; &amp; &apos;hi&apos;"),
            "say \"hello\" & 'hi'",
        )

    def test_handles_none(self):
        self.assertEqual(self.plain_label(None), "")

    def test_handles_empty_string(self):
        self.assertEqual(self.plain_label(""), "")

    def test_plain_text_unchanged(self):
        self.assertEqual(self.plain_label("Normal title"), "Normal title")

    # ------------------------------------------------------------------
    # Entity escaping
    # ------------------------------------------------------------------

    def _parse_xml(self, template_name, context):
        from xml.etree import ElementTree as ET

        xml_str = render_to_string(template_name, context)
        return ET.fromstring(xml_str), xml_str

    def _loc_labels(self, root):
        ns = {"j": "https://janeway.systems"}
        return [el.text or "" for el in root.findall(".//j:loc_label", ns)]

    @override_settings(URL_CONFIG="path")
    def test_news_title_with_ampersand_is_valid_xml_and_not_double_encoded(self):
        """A news title containing & must be single-encoded (&amp;) in the XML."""
        from datetime import datetime, timezone as dt_tz

        ctx = {
            "page_title": "News",
            "h1": "News",
            "sitemap_level": "press-news",
            "parent_sitemap": {
                "loc": "http://example.com/sitemap.xml",
                "label": "Press",
            },
            "owner": self.press,
            "news_items": [
                {
                    "url": "http://example.com/news/1/",
                    "posted": datetime(2024, 1, 1, tzinfo=dt_tz.utc),
                    "title": "Cats & Dogs",
                }
            ],
        }
        root, xml_str = self._parse_xml("common/news_sitemap.xml", ctx)
        self.assertNotIn("&amp;amp;", xml_str)
        self.assertIn("Cats & Dogs", self._loc_labels(root))

    @override_settings(URL_CONFIG="path")
    def test_article_title_with_html_is_plain_text_in_xml(self):
        """An article title with HTML markup is stored as plain text in the XML."""
        from utils.logic import _plain_label

        ctx = build_issue_sitemap_context(self.issue_one, self.journal_one)
        ctx["article_entries"][0]["title"] = _plain_label("<em>Test &amp; Article</em>")
        root, xml_str = self._parse_xml("common/issue_sitemap.xml", ctx)
        self.assertNotIn("&amp;amp;", xml_str)
        self.assertNotIn("&lt;em&gt;", xml_str)
        self.assertIn("Test & Article", self._loc_labels(root))

    @override_settings(URL_CONFIG="path")
    def test_pages_label_with_special_chars_is_valid_xml(self):
        """A pages-sitemap label containing < > & produces well-formed XML."""
        ctx = {
            "page_title": "Pages",
            "h1": "Pages",
            "sitemap_level": "press-pages",
            "parent_sitemap": {
                "loc": "http://example.com/sitemap.xml",
                "label": "Press",
            },
            "links": [("http://example.com/about/", 'About "Us" & <More>', None)],
        }
        root, xml_str = self._parse_xml("common/pages_sitemap.xml", ctx)
        self.assertIn('About "Us" & <More>', self._loc_labels(root))

    # ------------------------------------------------------------------
    # URL completeness
    # ------------------------------------------------------------------

    def _rendered_locs(self, template_name, context):
        xml = render_to_string(template_name, context)
        soup = BeautifulSoup(xml, "xml")
        return {el.get_text(strip=True) for el in soup.find_all("loc")}

    @override_settings(URL_CONFIG="path")
    def test_press_sitemap_renders_all_child_locs(self):
        """press_sitemap.xml emits a <loc> for every entry in child_sitemaps."""
        ctx = build_press_index_context(self.press)
        self.assertTrue(
            ctx["child_sitemaps"], "No child_sitemaps — test would vacuously pass"
        )
        locs = self._rendered_locs("common/press_sitemap.xml", ctx)
        for child in ctx["child_sitemaps"]:
            self.assertIn(child["loc"], locs, f"Missing child loc: {child['loc']}")

    @override_settings(URL_CONFIG="path")
    def test_journal_sitemap_renders_all_child_locs(self):
        """level2_sitemap.xml emits a <loc> for every entry in child_sitemaps (journal)."""
        ctx = build_journal_index_context(self.journal_one)
        self.assertTrue(
            ctx["child_sitemaps"], "No child_sitemaps — test would vacuously pass"
        )
        locs = self._rendered_locs("common/level2_sitemap.xml", ctx)
        for child in ctx["child_sitemaps"]:
            self.assertIn(child["loc"], locs, f"Missing child loc: {child['loc']}")

    @override_settings(URL_CONFIG="path")
    def test_repo_sitemap_renders_all_child_locs(self):
        """level2_sitemap.xml emits a <loc> for every entry in child_sitemaps (repository)."""
        ctx = build_repo_index_context(self.repository)
        self.assertTrue(
            ctx["child_sitemaps"], "No child_sitemaps — test would vacuously pass"
        )
        locs = self._rendered_locs("common/level2_sitemap.xml", ctx)
        for child in ctx["child_sitemaps"]:
            self.assertIn(child["loc"], locs, f"Missing child loc: {child['loc']}")

    @override_settings(URL_CONFIG="path")
    def test_issue_sitemap_renders_all_article_locs(self):
        """issue_sitemap.xml emits a <loc> for every entry in article_entries."""
        ctx = build_issue_sitemap_context(self.issue_one, self.journal_one)
        self.assertTrue(
            ctx["article_entries"], "No article_entries — test would vacuously pass"
        )
        locs = self._rendered_locs("common/issue_sitemap.xml", ctx)
        for entry in ctx["article_entries"]:
            self.assertIn(entry["url"], locs, f"Missing article loc: {entry['url']}")

    @override_settings(URL_CONFIG="path")
    def test_news_sitemap_renders_all_news_locs(self):
        """news_sitemap.xml emits a <loc> for every entry in news_items."""
        from datetime import datetime, timezone as dt_tz

        news_url = "http://testpress.example.com/news/test-item/"
        ctx = {
            "page_title": "News Sitemap",
            "h1": "News Sitemap",
            "sitemap_level": "press-news",
            "parent_sitemap": {
                "loc": "http://testpress.example.com/sitemap.xml",
                "label": "Press",
            },
            "owner": self.press,
            "news_items": [
                {
                    "url": news_url,
                    "posted": datetime(2024, 1, 15, 12, 0, tzinfo=dt_tz.utc),
                    "title": "Test News Item",
                }
            ],
        }
        locs = self._rendered_locs("common/news_sitemap.xml", ctx)
        self.assertIn(news_url, locs)

    @override_settings(URL_CONFIG="path")
    def test_pages_sitemap_renders_all_page_locs(self):
        """pages_sitemap.xml emits a <loc> for every entry in links."""
        page_url = "http://testpress.example.com/about/"
        ctx = {
            "page_title": "Pages - Test Journal",
            "h1": "Pages - Test Journal",
            "sitemap_level": "journal-pages",
            "parent_sitemap": {
                "loc": "http://testpress.example.com/sitemap.xml",
                "label": "Journal",
            },
            "links": [(page_url, "About", None)],
        }
        locs = self._rendered_locs("common/pages_sitemap.xml", ctx)
        self.assertIn(page_url, locs)

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    _SCHEMA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from lxml import etree

        cls.urlset_schema = etree.XMLSchema(
            etree.parse(os.path.join(cls._SCHEMA_ROOT, "sitemap.xsd.xml"))
        )
        cls.siteindex_schema = etree.XMLSchema(
            etree.parse(os.path.join(cls._SCHEMA_ROOT, "siteindex.xsd.xml"))
        )

    def _validate(self, schema, template_name, context):
        from lxml import etree

        xml_str = render_to_string(template_name, context)
        doc = etree.parse(io.BytesIO(xml_str.encode("utf-8")))
        valid = schema.validate(doc)
        return valid, schema.error_log

    @override_settings(URL_CONFIG="path")
    def test_issue_sitemap_validates_against_urlset_schema(self):
        """A rendered issue sitemap (urlset) validates against sitemap.xsd."""
        ctx = {
            "page_title": "Sitemap - Journal One",
            "h1": "Sitemap - Journal One",
            "sitemap_level": "issue",
            "parent_sitemap": {
                "loc": "http://localhost:8000/tst/sitemap.xml",
                "label": "Journal One",
            },
            "article_entries": [
                {
                    "url": "http://localhost:8000/tst/article/id/1/",
                    "lastmod": "2024-01-15T12:00:00+00:00",
                    "title": "Test Article",
                }
            ],
            "issue": None,
            "journal": self.journal_one,
        }
        valid, errors = self._validate(
            self.urlset_schema, "common/issue_sitemap.xml", ctx
        )
        self.assertTrue(valid, str(errors))

    @override_settings(URL_CONFIG="path")
    def test_news_sitemap_validates_against_urlset_schema(self):
        """A rendered news sitemap (urlset) validates against sitemap.xsd."""
        from datetime import datetime, timezone as dt_tz

        ctx = {
            "page_title": "Sitemap - News",
            "h1": "Sitemap - News",
            "sitemap_level": "news",
            "parent_sitemap": {
                "loc": "http://localhost:8000/sitemap.xml",
                "label": "Press",
            },
            "owner": self.press,
            "news_items": [
                {
                    "url": "http://localhost:8000/news/1/",
                    "posted": datetime(2024, 1, 15, 12, 0, tzinfo=dt_tz.utc),
                    "title": "Test News Item",
                }
            ],
        }
        valid, errors = self._validate(
            self.urlset_schema, "common/news_sitemap.xml", ctx
        )
        self.assertTrue(valid, str(errors))

    @override_settings(URL_CONFIG="path")
    def test_press_sitemap_validates_against_siteindex_schema(self):
        """Press sitemapindex validates against siteindex.xsd."""
        ctx = build_press_index_context(self.press)
        valid, errors = self._validate(
            self.siteindex_schema, "common/press_sitemap.xml", ctx
        )
        self.assertTrue(valid, str(errors))

    @override_settings(URL_CONFIG="path")
    def test_journal_sitemap_validates_against_siteindex_schema(self):
        """Journal sitemapindex validates against siteindex.xsd."""
        ctx = build_journal_index_context(self.journal_one)
        valid, errors = self._validate(
            self.siteindex_schema, "common/level2_sitemap.xml", ctx
        )
        self.assertTrue(valid, str(errors))

    @override_settings(URL_CONFIG="path")
    def test_pages_sitemap_validates_against_urlset_schema(self):
        """A rendered pages sitemap (urlset) validates against sitemap.xsd."""
        from utils.logic import build_pages_sitemap_context

        ctx = build_pages_sitemap_context(self.journal_one)
        valid, errors = self._validate(
            self.urlset_schema, "common/pages_sitemap.xml", ctx
        )
        self.assertTrue(valid, str(errors))


class PreprintsUtilsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo_manager1 = helpers.create_user("repo_man@example.com")
        cls.repo_manager2 = helpers.create_user("repo_man2@example.com")
        cls.other_user = helpers.create_user("other@example.com")

        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.repo_manager1, cls.repo_manager2], []
        )

        cls.submitted_preprint = helpers.create_preprint(
            cls.repository, cls.other_user, cls.subject
        )

        cls.request = helpers.Request()
        cls.request.user = cls.other_user
        cls.request.repository = cls.repository
        cls.request.press = cls.press
        cls.request.site_type = cls.repository
        cls.request.model_content_type = ContentType.objects.get_for_model(
            cls.request.repository
        )


class PreprintsTransactionalEmailTests(PreprintsUtilsTests):
    def test_send_submission_notification_all_managers(self):
        kwargs = {"request": self.request, "preprint": self.submitted_preprint}

        preprint_submission(**kwargs)

        # There should be 3 emails sent 1 to author, 2 to managers
        self.assertEqual(len(mail.outbox), 3)

        expected_recipients = [self.repo_manager1.email, self.repo_manager2.email]
        self.assertIn(mail.outbox[1].to[0], expected_recipients)
        self.assertIn(mail.outbox[2].to[0], expected_recipients)

    def test_send_submission_notification_one(self):
        self.repository.submission_notification_recipients.add(self.repo_manager1)
        self.repository.save()

        kwargs = {"request": self.request, "preprint": self.submitted_preprint}

        preprint_submission(**kwargs)

        expected_recipients = [self.repo_manager1.email]

        self.assertEqual(len(expected_recipients), len(mail.outbox[1].to))
        for r in expected_recipients:
            self.assertIn(r, mail.outbox[1].to)


class AdminTestMeta(type):
    """A Metaclass for generating test cases directly from the admin registry

    A new test is generated for each admin class registered via the admin.py
    modules in the application
    ChildrenMustImplement: build_test_case
    """

    def __new__(cls, name, bases, attrs):
        def test_bar(instance):
            instance.assertTrue(False)

        for test_name, test_case in cls.build_tests():
            attrs[test_name] = test_case
        return type(name, bases, attrs)

    @classmethod
    def build_tests(cls):
        admin_registry = site._registry
        for model, admin_class in admin_registry.items():
            yield cls.build_test_case(model, admin_class)

    @classmethod
    def build_test_case(cls, model, admin_class):
        raise NotImplementedError()


class AdminSearchTestMeta(AdminTestMeta):
    def build_test_case(model, admin_class):
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        url_name = f"admin:{app_label}_{model_name}_changelist"
        url = reverse(url_name) + "?q=test"

        def test_case(instance):
            response = instance.client.get(
                url,
                SERVER_NAME=instance.press.domain,
            )
            instance.assertEqual(response.status_code, 200)

        test_name = f"test_admin_view_{app_label}_{model_name}"
        return test_name, test_case


class TestAdmin(TestCase, metaclass=AdminSearchTestMeta):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_model = get_user_model()
        cls.superuser = user_model.objects.create_superuser(
            username="super",
            password="secret",
            email="super@example.com",
        )
        cls.press = helpers.create_press()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.press.delete()
        cls.superuser.delete()

    def setUp(self):
        self.client.force_login(self.superuser)


class TestBounceEmailRoutes(UtilsTests):
    def test_send_bounce_notification_actor_is_editor(self):
        """
        Tests that when an email sent by an editor bounces the bounce
        notification is sent to that editor.
        """
        fake_log_entry = util_models.LogEntry.add_entry(
            "Test Log Entry",
            "This is a fake log entry",
            level="Info",
            actor=self.editor,
            target=self.submitted_article,
            is_email=True,
            to="tuvix@security.voyager.fed",
            message_id="12324343432",
            subject="This is all just a test",
        )
        logic.send_bounce_notification_to_event_actor(fake_log_entry)
        self.assertEqual(self.editor.email, mail.outbox[0].to[0])

    def test_send_bounce_notification_actor_is_author(self):
        """
        Tests that bounce emails are not sent to authors. They are instead
        directed to the press' primary contact.
        """
        fake_log_entry = util_models.LogEntry.add_entry(
            "Test Log Entry",
            "This is a fake log entry",
            level="Info",
            actor=self.author,
            target=self.submitted_article,
            is_email=True,
            to="tuvix@security.voyager.fed",
            message_id="12324343432",
            subject="This is all just a test",
        )
        logic.send_bounce_notification_to_event_actor(fake_log_entry)
        self.assertEqual(self.press.main_contact, mail.outbox[0].to[0])

    def test_mailgun_webhook(self):
        message_id = "12324343432"
        fake_log_entry = util_models.LogEntry.add_entry(
            "Test Log Entry",
            "This is a fake log entry",
            level="Info",
            actor=self.editor,
            target=self.submitted_article,
            is_email=True,
            to="tuvix@security.voyager.fed",
            message_id=message_id,
            subject="This is all just a test",
        )
        fake_mailgun_post = {
            "Message-Id": message_id,
            "token": "122112",
            "timestamp": timezone.now(),
            "signature": "dsfsfsdfsdfsdfds",
            "event": "dropped",
        }
        logic.parse_mailgun_webhook(fake_mailgun_post)
        self.assertEqual(self.editor.email, mail.outbox[0].to[0])


class TestMigrationUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.setting = helpers.create_setting()
        cls.setting_value = cls.setting.settingvalue_set.first()

    def test_update_default_setting_values(self):
        with translation.override("en"):
            new_value = "Updated default setting value"
            migration_utils.update_default_setting_values(
                apps,
                self.setting.name,
                self.setting.group.name,
                values_to_replace=["Default setting value"],
                replacement_value=new_value,
            )
            saved_value = setting_handler.get_setting(
                self.setting.group.name,
                self.setting.name,
                None,
            ).processed_value
            self.assertEqual(
                new_value,
                saved_value,
            )


class TestORCiDRecord(TestCase):
    all_fields = helpers.get_orcid_record_all_fields()
    min_fields = helpers.get_orcid_record_min_fields()

    @mock.patch("utils.orcid.get_orcid_record", return_value=all_fields)
    def test_record_details_all(self, mock_record):
        details = get_orcid_record_details("0000-0000-0000-0000")
        self.assertEqual(details["orcid"], "0000-0000-0000-0000")
        self.assertEqual(details["uri"], "http://sandbox.orcid.org/0000-0000-0000-0000")
        self.assertEqual(details["first_name"], "cdleschol")
        self.assertEqual(details["last_name"], "arship")
        self.assertEqual(len(details["emails"]), 1)
        self.assertEqual(details["emails"][0], "cdleschol@mailinator.com")
        self.assertEqual(details["affiliation"], "California Digital Library")
        self.assertEqual(details["country"], "US")

    @mock.patch("utils.orcid.get_orcid_record", return_value=min_fields)
    def test_record_details_min(self, mock_record):
        details = get_orcid_record_details("0000-0000-0000-0000")
        self.assertEqual(details["orcid"], "0000-0000-0000-0000")
        self.assertEqual(details["uri"], "http://sandbox.orcid.org/0000-0000-0000-0000")
        self.assertIsNone(details["first_name"])
        self.assertIsNone(details["last_name"])
        self.assertEqual(len(details["emails"]), 0)
        self.assertIsNone(details["affiliation"])
        self.assertIsNone(details["country"])

    @mock.patch("utils.orcid.get_orcid_record", return_value=None)
    def test_record_details_empty_on_lookup_failure(self, mock_record):
        details = get_orcid_record_details("0000-0000-0000-0000")
        self.assertFalse(details)
        self.assertEqual(len(details), 0)

    @override_settings(URL_CONFIG="domain")
    @mock.patch("utils.logic.get_current_request")
    def test_redirect_uri(self, get_current_request):
        press = helpers.create_press()
        repo, _subject = helpers.create_repository(press, [], [])
        request = helpers.Request()
        request.site_type = repo
        get_current_request.return_value = request
        self.assertEqual(
            build_redirect_uri(repo), "http://repo.domain.com/login/orcid/"
        )


class URLLogicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # The raw unicode string of a 'next' URL
        cls.next_url_raw = "/target/page/?a=b&x=y"
        # The above string url-encoded with safe='/'
        cls.next_url_encoded = "/target/page/%3Fa%3Db%26x%3Dy"
        # The above string prepended with 'next='
        cls.next_url_query_string = "next=/target/page/%3Fa%3Db%26x%3Dy"
        # The core_login url with encoded next url
        cls.core_login_with_next = "/login/?next=/target/page/%3Fa%3Db%26x%3Dy"

    def test_build_url_query_as_querydict(self):
        querydict = QueryDict("a=b&a=c", mutable=True)
        querydict.update({"next": self.next_url_raw})
        url = logic.build_url(
            "example.org",
            scheme="https",
            path="/path/",
            query=querydict,
        )
        self.assertEqual(
            url,
            "https://example.org/path/?a=b&a=c&next=/target/page/%3Fa%3Db%26x%3Dy",
        )

    def test_build_url_query_as_plain_dict(self):
        plain_dict = {
            "a": "b",
            "next": self.next_url_raw,
        }
        url = logic.build_url(
            "example.org",
            scheme="https",
            path="/path/",
            query=plain_dict,
        )
        self.assertEqual(
            url,
            "https://example.org/path/?a=b&next=/target/page/%3Fa%3Db%26x%3Dy",
        )

    def test_build_url_query_as_string(self):
        query_string = f"a=b&a=c&{self.next_url_query_string}"
        url = logic.build_url(
            "example.org",
            scheme="https",
            path="/path/",
            query=query_string,
        )
        self.assertEqual(
            url,
            "https://example.org/path/?a=b&a=c&next=/target/page/%3Fa%3Db%26x%3Dy",
        )

    def test_add_query_parameters_to_url(self):
        url = "https://example.org/path/?a=b&a=c"
        new_url = logic.add_query_parameters_to_url(
            url,
            {"next": self.next_url_raw},
        )
        self.assertEqual(
            f"https://example.org/path/?a=b&a=c&{self.next_url_query_string}",
            new_url,
        )

    def test_orcid_encode_state(self):
        result = encode_state(self.next_url_raw, "login")
        expected = f"next={self.next_url_encoded}&action=login"
        self.assertEqual(result, expected)

    def test_orcid_decode_state(self):
        result = decode_state(f"next={self.next_url_encoded}&action=register")
        expected = {"next": [self.next_url_raw], "action": ["register"]}
        self.assertDictEqual(result, expected)


class TestRORImport(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ror_records = helpers.get_ror_records()

    def test_filter_new_records(self):
        existing_rors = {
            "00j1xwp39": "2013-12-10",
        }
        new_records = models.RORImport.filter_new_records(
            self.ror_records,
            existing_rors,
        )
        self.assertListEqual(
            [os.path.split(record.get("id"))[-1] for record in new_records],
            ["013yz9b19", "035dkdb55"],
        )

    def test_filter_updated_records(self):
        existing_rors = {
            "00j1xwp39": "2013-12-10",
            "013yz9b19": "2024-12-10",
            "035dkdb55": "2024-12-12",
        }
        updated_records = models.RORImport.filter_updated_records(
            self.ror_records,
            existing_rors,
        )
        self.assertListEqual(
            [os.path.split(record.get("id"))[-1] for record in updated_records],
            ["00j1xwp39", "013yz9b19"],
        )


class CheckMailgunStatCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.log_entry = models.LogEntry.add_entry(
            "Test Log Entry",
            "This is a fake log entry",
            level="Info",
            is_email=True,
            subject="This is all just a test",
            message_id="12345",
        )

    @override_settings(ENABLE_ENHANCED_MAILGUN_FEATURES=True)
    @mock.patch("utils.management.commands.check_mailgun_stat.get_logs")
    def test_status_delivered(self, get_logs):
        get_logs.return_value = {
            "items": [
                {
                    "event": "delivered",
                    "id": "hK7mQVt1QtqRiOfQXta4sw",
                    "timestamp": 1529692199.626182,
                    "log-level": "info",
                    "envelope": {
                        "transport": "smtp",
                        "sender": "sender@example.org",
                        "sending-ip": "123.123.123.123",
                        "targets": "john@example.com",
                    },
                    "flags": {
                        "is-routed": False,
                        "is-authenticated": False,
                        "is-system-test": False,
                        "is-test-mode": False,
                    },
                    "delivery-status": {
                        "tls": True,
                        "mx-host": "aspmx.l.example.com",
                        "code": 250,
                        "description": "",
                        "session-seconds": 0.4367079734802246,
                        "utf8": True,
                        "attempt-no": 1,
                        "message": "OK",
                        "certificate-verified": True,
                    },
                    "message": {
                        "headers": {
                            "to": "team@example.org",
                            "message-id": "20180622182958.1.48906CB188F1A454@exmple.org",
                            "from": "sender@exmple.org",
                            "subject": "Test Subject",
                        },
                        "attachments": [],
                        "size": 586,
                    },
                    "storage": {
                        "url": "https://storage-us-west1.api.mailgun.net/v3/domains/...",
                        "region": "us-west1",
                        "key": "AwABB...",
                        "env": "production",
                    },
                    "recipient": "john@example.com",
                    "recipient-domain": "example.com",
                    "recipient-provider": "Gmail",
                    "tags": [],
                    "user-variables": {},
                }
            ],
            "paging": {
                "next": "https://api.mailgun.net/v3/samples.mailgun.org/events/W3siY...",
                "previous": "https://api.mailgun.net/v3/samples.mailgun.org/events/Lkawm...",
            },
        }
        call_command("check_mailgun_stat")
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.message_status, "delivered")
        self.assertTrue(self.log_entry.status_checks_complete)

    @override_settings(ENABLE_ENHANCED_MAILGUN_FEATURES=True)
    @mock.patch("utils.logic.send_bounce_notification_to_event_actor")
    @mock.patch("utils.management.commands.check_mailgun_stat.get_logs")
    def test_status_failed(self, get_logs, send_bounce_notification):
        get_logs.return_value = {
            "items": [
                {
                    "event": "failed",
                    "id": "pl271FzxTTmGRW8Uj3dUWw",
                    "timestamp": 1529701969.818328,
                    "log-level": "error",
                    "severity": "permanent",
                    "reason": "suppress-bounce",
                    "envelope": {},
                    "flags": {
                        "is-routed": False,
                        "is-authenticated": True,
                        "is-system-test": False,
                        "is-test-mode": False,
                    },
                    "delivery-status": {},
                    "message": {
                        "headers": {
                            "to": "joan@example.com",
                            "message-id": "20180622211249.1.2A6098970A380E12@example.org",
                            "from": "john@example.org",
                            "subject": "Test Subject",
                        },
                        "attachments": [],
                        "size": 867,
                    },
                    "storage": {},
                    "recipient": "slava@mailgun.com",
                    "recipient-domain": "mailgun.com",
                    "recipient-provider": "Gmail",
                    "tags": [],
                    "user-variables": {},
                }
            ],
            "paging": {
                "next": "https://api.mailgun.net/v3/samples.mailgun.org/events/W3siY...",
                "previous": "https://api.mailgun.net/v3/samples.mailgun.org/events/Lkawm...",
            },
        }
        call_command("check_mailgun_stat")
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.message_status, "failed")
        self.assertTrue(self.log_entry.status_checks_complete)

    @override_settings(ENABLE_ENHANCED_MAILGUN_FEATURES=True)
    @mock.patch("utils.management.commands.check_mailgun_stat.get_logs")
    def test_status_accepted(self, get_logs):
        get_logs.return_value = {
            "items": [
                {
                    "event": "accepted",
                    "id": "jxVuhYlhReaK3QsggHfFRA",
                    "timestamp": 1529692198.641821,
                    "log-level": "info",
                    "method": "smtp",
                    "envelope": {
                        "targets": "team@example.org",
                        "transport": "smtp",
                        "sender": "sender@example.org",
                    },
                    "flags": {"is-authenticated": False},
                    "message": {
                        "headers": {
                            "to": "team@example.org",
                            "message-id": "20180622182958.1.48906CB188F1A454@exmple.org",
                            "from": "sender@example.org",
                            "subject": "Test Subject",
                        },
                        "attachments": [],
                        "recipients": ["team@example.org"],
                        "size": 586,
                    },
                    "storage": {
                        "url": "https://se.api.mailgun.net/v3/domains/example.org/messages/eyJwI...",
                        "key": "eyJwI...",
                    },
                    "recipient": "team@example.org",
                    "recipient-domain": "example.org",
                    "tags": [],
                    "user-variables": {},
                }
            ],
            "paging": {
                "next": "https://api.mailgun.net/v3/samples.mailgun.org/events/W3siY...",
                "previous": "https://api.mailgun.net/v3/samples.mailgun.org/events/Lkawm...",
            },
        }
        call_command("check_mailgun_stat")
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.message_status, "accepted")


class DefaultSettingsIntegrityTests(TestCase):
    """Guards against malformed entries in journal_defaults.json.

    A botched merge once fused two setting entries together, producing
    duplicate JSON keys. The file still parsed, but the duplicated keys
    silently dropped a setting, which only surfaced as DoesNotExist errors
    deep in unrelated tests. These checks fail fast and point at the file.
    """

    @classmethod
    def setUpTestData(cls):
        cls.file_path = os.path.join(
            settings.BASE_DIR,
            "utils/install/journal_defaults.json",
        )
        with codecs.open(cls.file_path, encoding="utf-8") as json_data:
            cls.raw = json_data.read()

    def reject_duplicate_keys(self, pairs):
        keys = [key for key, value in pairs]
        duplicates = [key for key in set(keys) if keys.count(key) > 1]
        if duplicates:
            raise AssertionError(
                "Duplicate keys {} in journal_defaults.json object {}".format(
                    duplicates, dict(pairs)
                )
            )
        return dict(pairs)

    def test_no_duplicate_keys(self):
        # object_pairs_hook runs for every object, so a duplicate key
        # anywhere in the file raises rather than silently winning.
        json.loads(self.raw, object_pairs_hook=self.reject_duplicate_keys)

    def test_every_setting_is_well_formed(self):
        default_data = json.loads(self.raw)
        for item in default_data:
            self.assertIn("group", item)
            self.assertIn("setting", item)
            self.assertIn("value", item)
            self.assertTrue(item["group"].get("name"))
            self.assertTrue(item["setting"].get("name"))
            self.assertTrue(item["setting"].get("type"))

    def test_setting_names_are_unique_within_group(self):
        default_data = json.loads(self.raw)
        seen = set()
        for item in default_data:
            key = (item["group"]["name"], item["setting"]["name"])
            self.assertNotIn(
                key,
                seen,
                msg="Duplicate setting {} in journal_defaults.json".format(key),
            )
            seen.add(key)

    def test_author_affiliation_dates_setting_present(self):
        # Regression check for the specific setting dropped by the merge.
        default_data = json.loads(self.raw)
        matches = [
            item
            for item in default_data
            if item["group"]["name"] == "metadata"
            and item["setting"]["name"] == "author_affiliation_dates"
        ]
        self.assertEqual(len(matches), 1)
