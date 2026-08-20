import re

import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import get_resolver

from core import include_urls as core_include_urls
from core import models, validators
from journal.tests.utils import make_test_journal
from utils.testing import helpers

# Extracts the literal leading path segment from a URL pattern's str()
# representation (works for both re_path regex strings and path() routes).
TOP_LEVEL_PREFIX_RE = re.compile(r"^\^?/?([A-Za-z0-9_.\-]+)")


def _collect_top_level_prefixes(url_patterns):
    # press-level routes only.
    prefixes = set()
    for pattern in url_patterns:
        raw_pattern = str(pattern.pattern)
        match = TOP_LEVEL_PREFIX_RE.match(raw_pattern)
        if match:
            prefixes.add(match.group(1))
    return prefixes


class TestValidators(TestCase):
    def test_valid_file(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(
            extensions=valid_extensions,
            mimetypes=valid_mimetypes,
        )
        file_ = SimpleUploadedFile("test.tar.gz", content=None)
        try:
            validator(file_)
        except ValidationError as e:
            error = e
        else:
            error = None

        self.assertIsNone(error)

    def test_invalid_file_extension(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(extensions=valid_extensions)
        file_ = SimpleUploadedFile("test.tar.bz2", bytes())

        with self.assertRaises(ValidationError):
            validator(file_)

    def test_invalid_mime_type(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(mimetypes=valid_mimetypes)
        file_ = SimpleUploadedFile("test.gz", bytes())

        with self.assertRaises(ValidationError):
            validator(file_)

    def test_invalid_email_setting(self):
        test_value = "{% if val %} This template is missing an endif"
        with self.assertRaises(ValidationError):
            validators.validate_email_setting(test_value)

    def test_valid_email_setting(self):
        test_value = "{% if val %} This template is valid {% endif %}"
        try:
            validators.validate_email_setting(test_value)
        except ValidationError as e:
            error = error
        else:
            error = None
        self.assertIsNone(error)


class ReservedUrlPrefixesTests(TestCase):
    def test_static_list_covers_live_top_level_url_prefixes(self):
        live_prefixes = _collect_top_level_prefixes(
            get_resolver().url_patterns
        ) | _collect_top_level_prefixes(core_include_urls.urlpatterns)
        # Canary: guards against this test silently checking nothing again.
        self.assertIn("cms", live_prefixes)
        missing = live_prefixes - validators.RESERVED_URL_PREFIXES
        self.assertEqual(
            missing,
            set(),
            "New top-level URL prefixes exist in the URL conf but are "
            "missing from core.validators.RESERVED_URL_PREFIXES: %s" % missing,
        )


class IsReservedTests(TestCase):
    def test_reserved_lowercase(self):
        self.assertTrue(validators.is_reserved("cms"))

    def test_reserved_case_insensitive(self):
        self.assertTrue(validators.is_reserved("CMS"))

    def test_not_reserved(self):
        self.assertFalse(validators.is_reserved("myjournal"))

    def test_reserved_strips_whitespace(self):
        self.assertTrue(validators.is_reserved(" cms "))


class FindAvailableCodeTests(TestCase):
    def test_prefix_candidate_wins_when_available(self):
        suggestion = validators._find_available_code(
            "newcode", kind="journal", max_length=40, taken=set()
        )
        self.assertEqual(suggestion, "jnewcode")

    def test_falls_through_to_suffix_when_prefix_taken(self):
        suggestion = validators._find_available_code(
            "foo", kind="journal", max_length=40, taken={"jfoo"}
        )
        self.assertEqual(suggestion, "fooj")

    def test_falls_through_to_random_fallback_when_both_taken(self):
        suggestion = validators._find_available_code(
            "foo", kind="journal", max_length=40, taken={"jfoo", "fooj"}
        )
        self.assertIsNotNone(suggestion)
        self.assertEqual(len(suggestion), 4)
        self.assertFalse(validators.is_reserved(suggestion))
        self.assertNotIn(suggestion, {"jfoo", "fooj"})

    def test_returns_none_when_nothing_available(self):
        # Every candidate this generates — prefixed, suffixed, and all 50
        # random fallbacks — gets rejected by treating everything as
        # reserved, without needing to predict what those candidates are.
        with mock.patch("core.validators.is_reserved", return_value=True):
            suggestion = validators._find_available_code(
                "anything", kind="journal", max_length=40, taken=set()
            )
        self.assertIsNone(suggestion)


class HeldByTests(TestCase):
    def test_returns_journal_when_journal_codes_hold_it(self):
        result = validators._held_by("code", {"code"}, set())
        self.assertEqual(result, "journal")

    def test_returns_repository_when_repository_codes_hold_it(self):
        result = validators._held_by("code", set(), {"code"})
        self.assertEqual(result, "repository")

    def test_returns_none_when_free_in_both(self):
        result = validators._held_by("code", {"other"}, {"another"})
        self.assertIsNone(result)


class CodeErrorMessageTests(TestCase):
    def test_reserved_message_omits_suggestion_clause_when_none_available(self):
        message = validators._code_error_message("reserved", "cms", "journal", None)
        self.assertIn("built-in Janeway system page", message)
        self.assertIn("Please choose a different code.", message)
        self.assertNotIn("Try '", message)

    def test_reserved_message_includes_suggestion_clause_when_available(self):
        message = validators._code_error_message("reserved", "cms", "journal", "jcms")
        self.assertIn("Try 'jcms' instead", message)

    def test_already_taken_message_omits_suggestion_clause_when_none_available(self):
        message = validators._code_error_message("journal", "cms", "journal", None)
        self.assertIn("already in use by another journal", message)
        self.assertIn("Please choose a different code.", message)
        self.assertNotIn("Try '", message)

    def test_same_model_conflict_phrased_as_another(self):
        message = validators._code_error_message("journal", "cms", "journal", "cms2")
        self.assertIn("already in use by another journal", message)
        self.assertIn("Try 'cms2' instead", message)

    def test_cross_model_conflict_phrased_as_a(self):
        message = validators._code_error_message("repository", "cms", "journal", "cms2")
        self.assertIn("already in use by a repository", message)


class ValidateCodeTests(TestCase):
    """
    validate_code raises ValidationError, with message
    and `code` baked in, on failure; returns None on success.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()

    def test_valid_code_passes(self):
        self.assertIsNone(
            validators.validate_code("freecode", kind="journal", max_length=40)
        )

    def test_reserved_code_raises_with_reserved_code(self):
        with self.assertRaises(ValidationError) as context:
            validators.validate_code("cms", kind="journal", max_length=40)
        self.assertEqual(context.exception.code, "reserved")
        self.assertIn("built-in Janeway system page", str(context.exception))

    def test_journal_reports_same_model_conflict(self):
        make_test_journal(code="existing", domain="existing.example.org")
        with self.assertRaises(ValidationError) as context:
            validators.validate_code("existing", kind="journal", max_length=40)
        self.assertEqual(context.exception.code, "journal")
        self.assertIn("already in use by another journal", str(context.exception))

    def test_journal_reports_cross_model_conflict(self):
        repository, _ = helpers.create_repository(self.press, [], [])
        with self.assertRaises(ValidationError) as context:
            validators.validate_code(
                repository.short_name, kind="journal", max_length=40
            )
        self.assertEqual(context.exception.code, "repository")
        self.assertIn("already in use by a repository", str(context.exception))

    def test_repository_reports_same_model_conflict(self):
        repository, _ = helpers.create_repository(self.press, [], [])
        with self.assertRaises(ValidationError) as context:
            validators.validate_code(
                repository.short_name, kind="repository", max_length=15
            )
        self.assertEqual(context.exception.code, "repository")
        self.assertIn("already in use by another repository", str(context.exception))

    def test_repository_reports_cross_model_conflict(self):
        make_test_journal(code="jtaken", domain="jtaken.example.org")
        with self.assertRaises(ValidationError) as context:
            validators.validate_code("jtaken", kind="repository", max_length=15)
        self.assertEqual(context.exception.code, "journal")
        self.assertIn("already in use by a journal", str(context.exception))

    def test_exclude_pk_lets_instance_keep_its_own_code(self):
        journal = make_test_journal(code="ownedcode", domain="owned.example.org")
        self.assertIsNone(
            validators.validate_code(
                "ownedcode", kind="journal", max_length=40, exclude_pk=journal.pk
            )
        )
