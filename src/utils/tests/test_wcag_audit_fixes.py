__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from utils.shared import clear_cache
from utils.testing import helpers


class TargetSizeCssTests(SimpleTestCase):
    def test_material_menu_button_is_at_least_24px_wide(self):
        css = helpers.read_theme_asset("material", "assets/mat.css")
        self.assertIn(
            "nav a.sidenav-trigger {\n    padding-left: 12px;\n    margin-left: 6px;\n}",
            css,
        )

    def test_clarity_footer_link_rows_do_not_overlap(self):
        css = helpers.read_theme_asset("clarity", "assets/css/clarity.css")
        self.assertIn(
            ".site-footer .list-inline-item a {\n  margin-block: 0;\n}",
            css,
        )


class ReflowCssTests(SimpleTestCase):
    def test_clarity_reading_bar_bleeds_only_to_the_narrow_gutter(self):
        css = helpers.read_theme_asset("clarity", "assets/css/clarity.css")
        self.assertIn(
            "  .reading-options-bar {\n"
            "    margin-inline: calc(-1 * var(--spacing-md));\n"
            "  }",
            css,
        )


@override_settings(URL_CONFIG="domain")
class IssueLinkLabelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(
            cls.journal_one,
            stage="Published",
        )
        cls.article_two = helpers.create_article(
            cls.journal_one,
            stage="Published",
        )
        cls.issue_one = helpers.create_issue(
            cls.journal_one,
            vol=1,
            number=1,
            articles=[cls.article_one],
        )
        cls.issue_two = helpers.create_issue(
            cls.journal_one,
            vol=1,
            number=2,
            articles=[cls.article_two],
        )
        cls.journal_one.current_issue = cls.issue_two
        cls.journal_one.save()

    def setUp(self):
        clear_cache()

    def test_clean_current_issue_link_is_labelled_with_current_issue(self):
        response = self.client.get(
            reverse("journal_issues"),
            {"theme": "clean"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(
            response,
            f"aria-label='{self.issue_two.display_title_a11y} (1 items)'",
        )
        self.assertNotContains(response, "aria-label=' (")

    def test_material_issue_archive_links_are_labelled_with_their_own_issue(self):
        response = self.client.get(
            reverse("journal_issue", kwargs={"issue_id": self.issue_one.pk}),
            {"theme": "material"},
            SERVER_NAME=self.journal_one.domain,
        )
        for issue in [self.issue_one, self.issue_two]:
            self.assertContains(
                response,
                f"aria-label='{issue.display_title_a11y}'",
                count=1,
            )
        self.assertContains(response, '<div class="collection">')
        self.assertNotContains(response, '<ul class="collection">')


@override_settings(URL_CONFIG="domain")
class JournalLogoFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        clear_cache()

    def test_fallback_logo_has_alt_text(self):
        for theme in ["OLH", "material"]:
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("website_index"),
                    {"theme": theme},
                    SERVER_NAME=self.journal_one.domain,
                )
                self.assertContains(
                    response,
                    f'sample/janeway.png" alt="{self.journal_one.name}"',
                )


@override_settings(URL_CONFIG="domain")
class HomepageSearchBarLabelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_homepage_element(
            cls.journal_one,
            "Search Bar",
            "core/homepage_elements/search_bar.html",
        )

    def setUp(self):
        clear_cache()

    def test_olh_search_bar_input_has_label(self):
        response = self.client.get(
            reverse("website_index"),
            {"theme": "OLH"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(response, 'id="homepage-search-label"')
        self.assertContains(response, 'aria-labelledby="homepage-search-label"')
        self.assertContains(response, 'id="homepage-search-input"')


@override_settings(URL_CONFIG="domain")
class PageLanguageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        clear_cache()

    def test_olh_press_page_declares_its_language(self):
        response = self.client.get(
            reverse("website_index"),
            {"theme": "OLH"},
            SERVER_NAME=self.press.domain,
        )
        self.assertContains(response, '<html class="no-js" lang="en">')

    def test_journal_pages_declare_their_language(self):
        for theme, tag in [
            ("OLH", '<html class="no-js" lang="en">'),
            ("material", '<html lang="en">'),
        ]:
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("website_index"),
                    {"theme": theme},
                    SERVER_NAME=self.journal_one.domain,
                )
                self.assertContains(response, tag)


@override_settings(URL_CONFIG="domain", CAPTCHA_TYPE="simple_math")
class CleanPressContactTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        clear_cache()

    def test_clean_press_contact_uses_the_clean_grid(self):
        response = self.client.get(
            reverse("press_contact"),
            {"theme": "clean"},
            SERVER_NAME=self.press.domain,
        )
        self.assertContains(response, '<div class="col-md-8">')
        self.assertContains(response, "Press Representatives")
        self.assertNotContains(response, "large-8 columns")


@override_settings(URL_CONFIG="domain")
class ArticleFilterAccordionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        clear_cache()

    def test_olh_filter_accordion_item_is_presentational(self):
        response = self.client.get(
            reverse("journal_articles"),
            {"theme": "OLH"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(
            response,
            '<li class="accordion-item" data-accordion-item role="presentation">',
        )
