__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch

from django.shortcuts import Http404

from cms import views as cms_views
from cms.tests import test_models


class ViewTests(test_models.TestCaseWithCMSData):
    @patch("cms.views.render")
    def test_view_page_journal(self, render):
        cms_views.view_page(self.request_journal, "test-name")
        render.assert_called_with(
            self.request_journal, "cms/page.html", {"page": self.journal_cms_page}
        )

    @patch("cms.views.render")
    def test_view_page_press(self, render):
        cms_views.view_page(self.request_press, "test-name")
        render.assert_called_with(
            self.request_press, "press/cms/page.html", {"page": self.press_cms_page}
        )

    @patch("os.path.exists")
    @patch("cms.logic.get_custom_templates_path")
    @patch("cms.views.render")
    def test_view_page_press_custom_template(self, render, get_path, path_exists):
        get_path.return_value = "fake/path/to/custom"
        path_exists.return_value = True
        self.press_cms_page.template = "custom/my_template.html"
        self.press_cms_page.save()
        cms_views.view_page(self.request_press, "test-name")
        render.assert_called_with(
            self.request_press, "custom/my_template.html", {"page": self.press_cms_page}
        )
        self.press_cms_page.template = ""
        self.press_cms_page.save()

    @patch("cms.logic.get_custom_templates_path")
    @patch("cms.views.render")
    def test_view_page_no_custom_folder_set_raises_error(self, _render, get_path):
        self.press_cms_page.template = "custom/my_template.html"
        self.press_cms_page.save()
        get_path.return_value = ""
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_press, "test-name")
        self.press_cms_page.template = ""
        self.press_cms_page.save()

    @patch("os.path.exists")
    @patch("cms.logic.get_custom_templates_path")
    @patch("cms.views.render")
    def test_view_page_bad_custom_template_path_raises_error(
        self, _render, get_path, path_exists
    ):
        self.press_cms_page.template = "custom/my_template.html"
        self.press_cms_page.save()
        get_path.return_value = "fake/path/to/custom"
        path_exists.return_value = False
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_press, "test-name")
        self.press_cms_page.template = ""
        self.press_cms_page.save()

    def test_draft_page_without_access_code_raises_http404(self):
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_journal, "draft-page")

    def test_draft_page_with_wrong_access_code_raises_http404(self):
        self.request_journal.GET = {"access_code": "wrong-code"}
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_journal, "draft-page")

    @patch("cms.views.render")
    def test_draft_page_with_correct_access_code_renders(self, render):
        from cms.models import Page

        page = Page.objects.get(pk=self.journal_draft_page.pk)
        self.request_journal.GET = {"access_code": str(page.preview_token)}
        cms_views.view_page(self.request_journal, "draft-page")
        render.assert_called_once()

    def test_published_page_with_access_code_raises_http404(self):
        self.request_journal.GET = {"access_code": "some-code"}
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_journal, "test-name")

    def test_draft_page_token_changes_when_draft_status_toggled(self):
        page = self.journal_draft_page
        initial_token = page.preview_token

        page.is_draft = False
        page.save()

        page.is_draft = True
        page.save()

        self.assertNotEqual(
            initial_token,
            page.preview_token,
            "Preview token should change when page transitions back to draft",
        )

        old_token = initial_token
        new_token = page.preview_token

        self.request_journal.GET = {"access_code": str(old_token)}
        with self.assertRaises(Http404):
            cms_views.view_page(self.request_journal, "draft-page")

        self.request_journal.GET = {"access_code": str(new_token)}
        with patch("cms.views.render") as render:
            cms_views.view_page(self.request_journal, "draft-page")
            render.assert_called_once()
