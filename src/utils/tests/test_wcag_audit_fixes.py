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

    def test_clarity_press_footer_links_get_half_the_row(self):
        template = helpers.read_theme_asset(
            "clarity",
            "templates/elements/press_footer.html",
        )
        self.assertIn('<div class="col-md-6 text-right">', template)
        self.assertNotIn("col-md-5", template)


class ContrastCssTests(SimpleTestCase):
    def test_olh_foundation_palette_is_set_before_foundation(self):
        scss = helpers.read_theme_asset("OLH", "assets/scss/app.scss")
        palette = scss.index("  primary: #1373b3,\n  secondary: #767676,")
        self.assertLess(palette, scss.index("@import 'foundation';"))

    def test_olh_default_link_colours_meet_contrast(self):
        scss = helpers.read_theme_asset("OLH", "assets/scss/_variables.scss")
        self.assertNotIn("#2199e8", scss)
        self.assertIn("$link-color: #1373b3 !default;", scss)

    def test_material_overrides_materialize_default_colours(self):
        css = helpers.read_theme_asset("material", "assets/mat.css")
        for rule in [
            "a {\n  color: #0270a6;\n}",
            ".btn, .btn-small, .btn-large {\n  background-color: #1d7e75;\n}",
            ".collection .collection-item.active {\n  background-color: #1d7e75;\n}",
            "label,\n.input-field > label {\n  color: #767676;\n}",
        ]:
            with self.subTest(rule=rule):
                self.assertIn(rule, css)


class NonTextContrastCssTests(SimpleTestCase):
    def test_olh_form_controls_use_the_contrasting_border(self):
        variables = helpers.read_theme_asset("OLH", "assets/scss/_variables.scss")
        self.assertIn("$input-border-color: #8f8f8f !default;", variables)
        settings = helpers.read_theme_asset("OLH", "assets/scss/_settings.scss")
        self.assertIn("$input-border: 1px solid $input-border-color;", settings)
        self.assertIn(
            "$input-prefix-border: 1px solid $input-border-color;",
            settings,
        )

    def test_bootstrap_theme_form_controls_use_the_contrasting_border(self):
        for theme, path in [
            ("clean", "assets/css/clean.css"),
            ("clarity", "assets/css/clarity.css"),
        ]:
            with self.subTest(theme=theme):
                css = helpers.read_theme_asset(theme, path)
                self.assertIn(
                    ".form-control,\n.custom-select {\n  border-color: #8491a0;\n}",
                    css,
                )

    def test_material_field_underlines_use_the_contrasting_border(self):
        css = helpers.read_theme_asset("material", "assets/mat.css")
        self.assertIn(
            "textarea.materialize-textarea,\n"
            ".select-wrapper input.select-dropdown {\n"
            "  border-bottom-color: #949494;\n"
            "}",
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

    def test_olh_collections_page_clips_nested_row_gutters(self):
        scss = helpers.read_theme_asset("OLH", "assets/scss/app.scss")
        self.assertIn(".collections-page {\n    overflow-x: clip;\n}", scss)
        template = helpers.read_theme_asset(
            "OLH",
            "templates/journal/collections.html",
        )
        self.assertIn('<section id="content" class="collections-page">', template)


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

    def test_olh_press_page_declares_the_active_language(self):
        response = self.client.get(
            reverse("website_index"),
            {"theme": "OLH"},
            SERVER_NAME=self.press.domain,
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        self.assertContains(response, '<html class="no-js" lang="fr">')

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
