from django.conf import settings
from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.urls.base import clear_script_prefix

from utils.testing import helpers
from repository import models as rm


class TestRepositoryLanguages(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("lang_manager@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "lang-repo.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )

    def setUp(self):
        clear_script_prefix()
        self.repository.languages = ["en"]
        self.repository.default_language = "en"
        self.repository.save()

    @override_settings(URL_CONFIG="domain")
    def test_default_language_is_english(self):
        self.assertEqual(self.repository.default_language, "en")
        self.assertEqual(self.repository.languages, ["en"])

    @override_settings(URL_CONFIG="domain")
    def test_enable_language(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"enable": "es"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertIn("es", self.repository.languages)
        self.assertIn("en", self.repository.languages)

    @override_settings(URL_CONFIG="domain")
    def test_disable_language(self):
        self.repository.languages = ["en", "es"]
        self.repository.save()
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"disable": "es"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertNotIn("es", self.repository.languages)
        self.assertIn("en", self.repository.languages)

    @override_settings(URL_CONFIG="domain")
    def test_set_default_language(self):
        self.repository.languages = ["en", "es"]
        self.repository.save()
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"default": "es"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertEqual(self.repository.default_language, "es")

    @override_settings(URL_CONFIG="domain")
    def test_set_default_to_inactive_language_rejected(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"default": "de"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertEqual(self.repository.default_language, "en")

    @override_settings(URL_CONFIG="domain")
    def test_disable_all_languages_falls_back_to_default(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"disable": "en"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertIn(settings.LANGUAGE_CODE, self.repository.languages)

    @override_settings(URL_CONFIG="domain")
    def test_default_language_reset_when_disabled(self):
        self.repository.languages = ["en", "es"]
        self.repository.default_language = "es"
        self.repository.save()
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_languages"),
            {"disable": "es"},
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertEqual(self.repository.default_language, "en")


class TestPreprintTranslation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("lang_trans_mgr@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.author = helpers.create_user("lang_author@janeway.systems")
        cls.author.is_active = True
        cls.author.save()
        cls.server_name = "lang-trans.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.author,
            cls.subject,
        )

    def setUp(self):
        clear_script_prefix()

    def test_preprint_translation_saves(self):
        self.preprint.title_en = "English Title"
        self.preprint.title_es = "Título en Español"
        self.preprint.abstract_en = "English abstract"
        self.preprint.abstract_es = "Resumen en español"
        self.preprint.save()
        self.preprint.refresh_from_db()
        self.assertEqual(self.preprint.title_en, "English Title")
        self.assertEqual(self.preprint.title_es, "Título en Español")
        self.assertEqual(self.preprint.abstract_en, "English abstract")
        self.assertEqual(self.preprint.abstract_es, "Resumen en español")

    def test_translated_metadata_empty_for_single_language(self):
        self.repository.languages = ["en"]
        self.repository.save()
        self.preprint.repository = self.repository
        self.assertEqual(self.preprint.translated_metadata(), [])

    def test_translated_metadata_returns_entry_per_active_language(self):
        self.repository.languages = ["en", "es"]
        self.repository.save()
        self.preprint.repository = self.repository
        self.preprint.title_en = "English Title"
        self.preprint.title_es = "Título en Español"
        self.preprint.abstract_en = "English abstract"
        self.preprint.abstract_es = "Resumen en español"
        metadata = self.preprint.translated_metadata()
        self.assertEqual(len(metadata), 2)
        by_title = {entry["title"]: entry for entry in metadata}
        self.assertIn("English Title", by_title)
        self.assertIn("Título en Español", by_title)
        self.assertEqual(
            by_title["Título en Español"]["abstract"],
            "Resumen en español",
        )

    def test_form_shows_per_language_fields_when_multiple(self):
        from repository.forms import PreprintInfo

        self.repository.languages = ["en", "es"]
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertIn("title_en", form.fields)
        self.assertIn("title_es", form.fields)
        self.assertIn("abstract_en", form.fields)
        self.assertIn("abstract_es", form.fields)
        self.assertNotIn("title", form.fields)
        self.assertNotIn("abstract", form.fields)

    def test_form_shows_base_fields_when_single_language(self):
        from repository.forms import PreprintInfo

        self.repository.languages = ["en"]
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertIn("title", form.fields)
        self.assertIn("abstract", form.fields)
        self.assertNotIn("title_en", form.fields)
        self.assertNotIn("title_es", form.fields)

    def test_form_primary_language_title_required(self):
        from repository.forms import PreprintInfo

        self.repository.languages = ["en", "es"]
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertTrue(form.fields["title_en"].required)
        self.assertFalse(form.fields["title_es"].required)

    def test_form_required_title_follows_repository_default_language(self):
        from repository.forms import PreprintInfo

        self.repository.languages = ["en", "es"]
        self.repository.default_language = "es"
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertTrue(form.fields["title_es"].required)
        self.assertFalse(form.fields["title_en"].required)

    def test_form_language_dropdown_with_multiple_languages(self):
        from repository.forms import PreprintInfo

        self.repository.languages = ["en", "es"]
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertIn("language", form.fields)
        choice_values = [c[0] for c in form.fields["language"].choices]
        self.assertEqual(choice_values, ["en", "es"])

    def test_form_language_hidden_with_single_language(self):
        from repository.forms import PreprintInfo
        from django.forms import HiddenInput

        self.repository.languages = ["en"]
        self.repository.save()
        request = helpers.Request()
        request.press = self.press
        request.repository = self.repository
        form = PreprintInfo(
            instance=self.preprint,
            request=request,
            submission_type_slug=None,
        )
        self.assertIsInstance(form.fields["language"].widget, HiddenInput)
        self.assertEqual(form.initial["language"], "en")

    def test_version_form_shows_per_language_fields_when_multiple(self):
        from repository.forms import VersionForm

        self.repository.languages = ["en", "es"]
        self.repository.save()
        self.preprint.repository = self.repository
        form = VersionForm(preprint=self.preprint)
        self.assertIn("title_en", form.fields)
        self.assertIn("title_es", form.fields)
        self.assertIn("abstract_en", form.fields)
        self.assertIn("abstract_es", form.fields)
        self.assertNotIn("title", form.fields)
        self.assertNotIn("abstract", form.fields)

    def test_version_form_shows_base_fields_when_single_language(self):
        from repository.forms import VersionForm

        self.repository.languages = ["en"]
        self.repository.save()
        self.preprint.repository = self.repository
        form = VersionForm(preprint=self.preprint)
        self.assertIn("title", form.fields)
        self.assertIn("abstract", form.fields)
        self.assertNotIn("title_en", form.fields)
        self.assertNotIn("title_es", form.fields)


class TestRepositoryLanguageMiddleware(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("lang_mw_mgr@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "lang-mw.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )

    def setUp(self):
        clear_script_prefix()
        self.repository.languages = ["en", "es"]
        self.repository.default_language = "en"
        self.repository.save()

    @override_settings(URL_CONFIG="domain")
    def test_middleware_sets_available_languages(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse("repository_languages"),
            SERVER_NAME=self.server_name,
        )
        self.assertIn("en", response.wsgi_request.available_languages)
        self.assertIn("es", response.wsgi_request.available_languages)

    @override_settings(URL_CONFIG="domain")
    def test_middleware_sets_default_language(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse("repository_languages"),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.wsgi_request.default_language, "en")
