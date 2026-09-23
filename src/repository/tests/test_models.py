__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Andy Byers, Mauro Sanchez & Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from urllib.parse import urlparse

import mock
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls.base import clear_script_prefix

from utils.testing import helpers
from submission import models as sm
from repository import models as rm


class TestModels(TestCase):
    def setUp(self):
        helpers.create_roles(["author"])
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.request = helpers.Request()
        self.request.press = self.press
        self.request.journal = self.journal_one
        self.article_one = helpers.create_article(self.journal_one)
        self.repository, self.subject = helpers.create_repository(self.press, [], [])

        self.section = sm.Section.objects.filter(
            journal=self.journal_one,
        ).first()
        self.license = sm.Licence.objects.create(
            journal=self.journal_one,
            name="Test License",
            short_name="Test",
            url="https://janeway.systems",
        )

        self.preprint_author = helpers.create_user(
            username="repo_author@janeway.systems",
        )
        self.preprint_one = helpers.create_preprint(
            self.repository,
            self.preprint_author,
            self.subject,
            title="Preprint Number One",
        )
        self.preprint_two = helpers.create_preprint(
            self.repository,
            self.preprint_author,
            self.subject,
            title="Preprint Number Two",
        )

    @override_settings(BASE_DIR="/tmp/")
    def test_create_article(self):
        preprint_file = SimpleUploadedFile(
            "test1.txt",
            b"these are the file contents!",  # note the b in front of the string [bytes]
        )
        with mock.patch("core.file_system.JanewayFileSystemStorage.location", "/tmp/"):
            preprint_one_version_file = rm.PreprintFile.objects.create(
                preprint=self.preprint_one,
                file=preprint_file,
                original_filename="preprint_file.txt",
                mime_type="text/plain",
                size=10000,
            )
            preprint_one_version = rm.PreprintVersion.objects.create(
                preprint=self.preprint_one,
                version=1,
                title="Preprint Number One",
                file=preprint_one_version_file,
            )
            article = self.preprint_one.create_article(
                journal=self.journal_one,
                workflow_stage="Unassigned",
                journal_license=self.license,
                journal_section=self.section,
            )

            self.assertEqual(
                self.preprint_one.article,
                article,
            )
            self.assertEqual(
                self.preprint_one.title,
                article.title,
            )
            self.assertEqual(
                self.preprint_one.abstract,
                article.abstract,
            )

    def test_create_article_force(self):
        preprint_file = SimpleUploadedFile(
            "test1.txt",
            b"these are the file contents!",  # note the b in front of the string [bytes]
        )
        with mock.patch("core.file_system.JanewayFileSystemStorage.location", "/tmp/"):
            preprint_one_version_file = rm.PreprintFile.objects.create(
                preprint=self.preprint_one,
                file=preprint_file,
                original_filename="preprint_file.txt",
                mime_type="text/plain",
                size=10000,
            )
            preprint_one_version = rm.PreprintVersion.objects.create(
                preprint=self.preprint_one,
                version=1,
                title="Preprint Number One",
                file=preprint_one_version_file,
            )
            article_one = self.preprint_one.create_article(
                journal=self.journal_one,
                workflow_stage="Unassigned",
                journal_license=self.license,
                journal_section=self.section,
            )
            article_two = self.preprint_one.create_article(
                journal=self.journal_one,
                workflow_stage="Unassigned",
                journal_license=self.license,
                journal_section=self.section,
                force=True,
            )
            self.assertNotEqual(
                article_one,
                article_two,
            )
            self.assertEqual(
                self.preprint_one.article,
                article_two,
            )


class PreprintURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_roles(["author"])
        cls.press = helpers.create_press()
        cls.repository, cls.subject = helpers.create_repository(cls.press, [], [])
        cls.preprint_author = helpers.create_user(
            username="preprint_url_author@janeway.systems",
        )
        cls.preprint_one = helpers.create_preprint(
            cls.repository,
            cls.preprint_author,
            cls.subject,
        )

    def setUp(self):
        cache.clear()
        clear_script_prefix()

    def tearDown(self):
        clear_script_prefix()
        cache.clear()
        helpers.clear_current_request()

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_preprint_url_generated_in_path_mode_is_not_reused_in_domain_mode(self):
        path_mode_request = helpers.browse(
            f"http://{self.press.domain}/{self.repository.short_name}/",
        )
        self.assertEqual(path_mode_request.site_object, self.repository)
        path_mode_url = self.preprint_one.url
        self.assertIn(
            f"/{self.repository.short_name}",
            urlparse(path_mode_url).path,
        )

        domain_mode_request = helpers.browse(
            f"http://{self.repository.domain}/",
        )
        self.assertEqual(domain_mode_request.site_object, self.repository)
        expected_url = f"http://{self.repository.domain}{self.preprint_one.local_url}"
        self.assertEqual(self.preprint_one.url, expected_url)

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_preprint_url_without_request_unaffected_by_path_mode_render(self):
        helpers.browse(f"http://{self.press.domain}/{self.repository.short_name}/")
        path_mode_url = self.preprint_one.url
        self.assertIn(
            f"/{self.repository.short_name}",
            urlparse(path_mode_url).path,
        )

        helpers.clear_current_request()
        clear_script_prefix()
        expected_url = f"http://{self.repository.domain}{self.preprint_one.local_url}"
        self.assertEqual(self.preprint_one.url, expected_url)
