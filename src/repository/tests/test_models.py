__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Andy Byers, Mauro Sanchez & Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import mock
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

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


class TestRepositoryOrganisationUnit(TestCase):
    """Tests for the RepositoryOrganisationUnit model introduced in iowa-and-isolinear."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repository, _ = helpers.create_repository(
            cls.press, [], [], domain="rou-test.domain.com"
        )
        cls.root = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Root",
            code="root",
        )
        cls.child_a = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Child A",
            code="child-a",
            parent=cls.root,
        )
        cls.child_b = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Child B",
            code="child-b",
            parent=cls.root,
        )
        cls.grandchild = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Grandchild",
            code="grandchild",
            parent=cls.child_a,
        )

    def test_get_descendants_returns_all_levels(self):
        """get_descendants returns children and grandchildren recursively."""
        descendants = self.root.get_descendants()
        self.assertIn(self.child_a, descendants)
        self.assertIn(self.child_b, descendants)
        self.assertIn(self.grandchild, descendants)

    def test_get_descendants_excludes_self(self):
        """get_descendants does not include the unit itself."""
        descendants = self.root.get_descendants()
        self.assertNotIn(self.root, descendants)

    def test_get_descendants_of_leaf_is_empty(self):
        """get_descendants on a leaf node returns an empty list."""
        self.assertEqual(self.grandchild.get_descendants(), [])

    def test_unique_together_code_and_repository(self):
        """Two ROUs in the same repository cannot share a code."""
        with self.assertRaises(IntegrityError):
            rm.RepositoryOrganisationUnit.objects.create(
                repository=self.repository,
                name="Duplicate",
                code="root",
            )

    def test_same_code_allowed_in_different_repository(self):
        """The same code is allowed in a different repository."""
        other_repo, _ = helpers.create_repository(
            self.press, [], [], domain="rou-other.domain.com"
        )
        unit = rm.RepositoryOrganisationUnit.objects.create(
            repository=other_repo,
            name="Root",
            code="root",
        )
        self.assertEqual(unit.code, "root")

    def test_str_includes_repository_code_and_unit_code(self):
        """__str__ returns a readable identifier."""
        result = str(self.root)
        self.assertIn(self.repository.code, result)
        self.assertIn("root", result)


class TestRepositorySubmissionType(TestCase):
    """Tests for the RepositorySubmissionType model introduced in iowa-and-isolinear."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repository, _ = helpers.create_repository(
            cls.press, [], [], domain="subtype-test.domain.com"
        )

    def _make_type(self, pill_colour="#1e40af"):
        return rm.RepositorySubmissionType(
            repository=self.repository,
            name="Article",
            name_plural="Articles",
            slug="article",
            pill_colour=pill_colour,
        )

    def test_valid_six_digit_hex_passes_validation(self):
        obj = self._make_type("#1e40af")
        obj.full_clean()  # should not raise

    def test_valid_three_digit_hex_passes_validation(self):
        obj = self._make_type("#fff")
        obj.full_clean()  # should not raise

    def test_invalid_hex_fails_validation(self):
        obj = self._make_type("blue")
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_hex_without_hash_fails_validation(self):
        obj = self._make_type("1e40af")
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_str_returns_name(self):
        obj = self._make_type()
        self.assertEqual(str(obj), "Article")
