__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import translation

from journal.middleware import JournalLocaleMiddleware
from utils.language import find_language_or_its_variant
from utils.testing import helpers


class JournalLocaleMiddlewareTests(TestCase):
    """Language constraint on journal sites (#4313)."""

    @classmethod
    def setUpTestData(cls):
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = JournalLocaleMiddleware(
            get_response=lambda request: HttpResponse(),
        )
        self.addCleanup(translation.deactivate)

    def activate_language(self, journal, accept_language):
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
        request.journal = journal
        self.middleware.process_request(request)
        return request

    def test_browser_language_not_offered_falls_back_to_default(self):
        helpers.set_journal_languages(
            self.journal_one,
            available=["es"],
            default="es",
        )
        request = self.activate_language(self.journal_one, "en")
        self.assertEqual(request.LANGUAGE_CODE, "es")

    def test_browser_language_offered_is_honoured(self):
        helpers.set_journal_languages(
            self.journal_one,
            available=["en", "es"],
            default="en",
        )
        request = self.activate_language(self.journal_one, "es")
        self.assertEqual(request.LANGUAGE_CODE, "es")

    def test_unconfigured_journal_constrains_to_default(self):
        # journal_two is left with the shipped defaults (journal_languages=[]
        # and default_journal_language="en"), the configuration of nearly every
        # existing journal. The browser's Accept-Language must be ignored.
        request = self.activate_language(self.journal_two, "fr")
        self.assertEqual(request.LANGUAGE_CODE, "en")
        self.assertEqual(request.available_languages, {"en"})

    def test_no_journal_falls_through_to_django_default(self):
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="fr")
        request.journal = None
        self.middleware.process_request(request)
        self.assertEqual(request.LANGUAGE_CODE, "fr")

    def test_resolves_language_variant(self):
        self.assertEqual(
            find_language_or_its_variant("en-GB", ["es", "en-US"]),
            "en-US",
        )
        self.assertIsNone(find_language_or_its_variant("de", ["en", "es"]))
