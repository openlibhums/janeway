from datetime import datetime, timedelta

from mock import patch
import pytz
from django.utils import timezone
from django.test import TestCase, override_settings
from django.urls import set_script_prefix
from freezegun import freeze_time

from django.template.loader import render_to_string

from utils.testing import helpers
from core import models as core_models
from core.templatetags import alt_text, fqdn, dates, latex_mathml
from django.test import TestCase, override_settings, RequestFactory
from django.utils.translation import activate
from django.conf import settings
from django.template.exceptions import TemplateSyntaxError
from utils import setting_handler


class TestFqdn(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.domain_journal, cls.path_journal = helpers.create_journals()
        cls.path_journal.domain = None
        cls.path_journal.save()

    def test_stateless_site_url_for_press(self):
        url_name = "press_all_users"
        url = fqdn.stateless_site_url(self.press, url_name)
        self.assertEqual(url, "http://localhost/press/user/all/")

    @override_settings(URL_CONFIG="domain")
    def test_stateless_site_url_for_journal_domain(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.domain_journal, url_name)
        self.assertEqual(url, f"http://{self.domain_journal.domain}/user/all/")

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_for_journal_path(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.path_journal, url_name)
        self.assertEqual(
            url,
            f"http://{self.path_journal.press.domain}/{self.path_journal.code}/user/all/",
        )

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_across_journals(self):
        url_name = "journal_users"
        fake_code = "fake_code"
        set_script_prefix(f"/{fake_code}")
        url = fqdn.stateless_site_url(self.path_journal, url_name)
        self.assertFalse(fake_code in url)
        self.assertEqual(
            url,
            f"http://{self.path_journal.press.domain}/{self.path_journal.code}/user/all/",
        )


ny_tz = pytz.timezone("America/New_York")
frozen_dt = timezone.make_aware(
    datetime(2025, 3, 26, 12, 0, 0),
    timezone=ny_tz,
)


@freeze_time(frozen_dt)
class TestOffsetDateTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_default = helpers.create_user("default@example.com")
        cls.user_tz = helpers.create_user(
            "tz@example.com",
            preferred_timezone="Europe/London",
        )
        cls.user_bad_tz = helpers.create_user(
            "bad@example.com",
            preferred_timezone="MemoryAlpha/Library",
        )

        cls.request_default = type("Request", (), {"user": cls.user_default})()
        cls.request_tz = type("Request", (), {"user": cls.user_tz})()
        cls.request_bad_tz = type("Request", (), {"user": cls.user_bad_tz})()

    def test_offset_date_with_default_timezone_datetime(self):
        """
        Test offset_date tag with default timezone and datetime-local input.
        """
        context = {"request": self.request_default}
        result = dates.offset_date(
            context,
            days=2,
            input_type="datetime-local",
        )
        expected = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(result, expected)

    def test_offset_date_with_preferred_timezone_datetime(self):
        """
        Test offset_date tag with a valid preferred timezone and datetime-local input.
        """
        context = {"request": self.request_tz}
        london = pytz.timezone("Europe/London")
        expected_due = timezone.now().astimezone(london) + timedelta(days=1)
        expected = expected_due.strftime("%Y-%m-%dT%H:%M")

        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        self.assertEqual(result, expected)

    def test_offset_date_with_invalid_timezone_datetime(self):
        """
        Test offset_date tag with an invalid preferred timezone and datetime-local input.
        Should fall back to default timezone.
        """
        context = {"request": self.request_bad_tz}
        expected = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        self.assertEqual(result, expected)

    def test_offset_date_with_default_timezone_date(self):
        """
        Test offset_date tag with default timezone and date input.
        """
        context = {"request": self.request_default}
        expected = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        result = dates.offset_date(
            context,
            days=2,
            input_type="date",
        )
        self.assertEqual(result, expected)


class TestDateHuman(TestCase):
    # Define the languages we want to test
    test_languages = {
        "en": "English",
        "en-us": "English (US)",
        "fr": "French",
        "de": "German",
        "nl": "Dutch",
        "cy": "Welsh",
        "es": "Spanish",
    }

    @classmethod
    def setUpTestData(cls):
        """sets up all the data for testing"""
        cls.test_dates = {
            "date": datetime(2023, 12, 3),  # 3 December 2023
            "leap_year": datetime(2024, 2, 29),  # 29 February 2024
            "new_year": datetime(2021, 1, 1),  # 1 January 2021
        }
        cls.expected_formats = {
            "date": {
                "en": "3 December 2023",
                "en-us": "3 December 2023",
                "fr": "3 décembre 2023",
                "de": "3 Dezember 2023",
                "nl": "3 december 2023",
                "cy": "3 Rhagfyr 2023",
                "es": "3 diciembre 2023",
            },
            "leap_year": {
                "en": "29 February 2024",
                "en-us": "29 February 2024",
                "fr": "29 février 2024",
                "de": "29 Februar 2024",
                "nl": "29 februari 2024",
                "cy": "29 Chwefror 2024",
                "es": "29 febrero 2024",
            },
            "new_year": {
                "en": "1 January 2021",
                "en-us": "1 January 2021",
                "fr": "1 janvier 2021",
                "de": "1 Januar 2021",
                "nl": "1 januari 2021",
                "cy": "1 Ionawr 2021",
                "es": "1 enero 2021",
            },
        }
        cls.test_non_dates = {
            "empty_string": "",
            "string": "2023,12,3",
            "int": 134567,
            "zero": 0,
            "none": None,
        }

    def test_non_dates_debug_true(self):
        """Test date_human hides input errors except when settings.DEBUG=True."""
        with override_settings(DEBUG=True):
            for key, test_non_date in self.test_non_dates.items():
                with self.subTest(non_date=key):
                    with self.assertRaises(TemplateSyntaxError) as context:
                        dates.date_human(test_non_date)
                    self.assertEqual(
                        str(context.exception),
                        "The value filtered by `date_human` must be a `datetime.datetime`",
                        f"Failed for non-existent date '{key}' . Expected TemplateSyntaxError.",
                    )

    def test_non_dates_debug_false(self):
        """Test date_human hides input errors except when settings.DEBUG=False."""
        with override_settings(DEBUG=False):
            for key, test_non_date in self.test_non_dates.items():
                with self.subTest(non_date=key):
                    result = dates.date_human(test_non_date)
                    self.assertEqual(
                        result,
                        "",
                        f"Failed for {key}.  Expected hidden error (i.e. empty string), actual '{result}'.",
                    )

    @override_settings(LANGUAGES=test_languages)
    def test_date_human_all_languages(self):
        """Test date_human with all supported languages that have complete test data"""
        for key, test_date in self.test_dates.items():
            for lang_code, expected in self.expected_formats[key].items():
                with self.subTest(date=key, code=lang_code):
                    activate(lang_code)
                    result = dates.date_human(test_date)
                    expected = self.expected_formats[key].get(lang_code)
                    self.assertEqual(
                        result,
                        expected,
                        f"Failed for {lang_code}.  Expected '{expected}', actual '{result}'.",
                    )

    @override_settings(LANGUAGES=test_languages)
    def test_date_human_browser_languages(self):
        """Test data_human uses application language regardless of browser language setting"""
        supported_languages = list(self.test_languages.keys())

        non_supported_languages = ["ja", "en-nz", "es-ni", "ar-sa"]

        browser_languages = supported_languages + non_supported_languages

        factory = RequestFactory()

        def set_browser_lang(lang_code):
            request = factory.get("/")
            request.META["HTTP_ACCEPT_LANGUAGE"] = lang_code

        for lang in browser_languages:
            set_browser_lang(lang)
            self.test_date_human_all_languages()


class TestProfileImageAltText(TestCase):
    """Covers the stored-alt-text lookup for Account.profile_image
    added for #5453."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.user = helpers.create_user(
            "profile_alt_text@example.org",
            first_name="Kathryn",
            last_name="Janeway",
        )
        cls.user.profile_image.name = "profile/kathryn.png"
        cls.user.save()

    def render_partial(self):
        return render_to_string(
            "common/elements/profile_image.html",
            {
                "user": self.user,
                "classes": "editorial-image",
            },
        )

    def test_profile_image_uses_stored_alt_text(self):
        core_models.AltText.objects.create(
            file_path=alt_text.encode_file_path(self.user.profile_image),
            alt_text="Kathryn smiling in the ready room",
        )
        rendered = self.render_partial()
        self.assertIn("Kathryn smiling in the ready room", rendered)
        self.assertNotIn(", profile image", rendered)

    def test_profile_image_falls_back_to_default_alt_text(self):
        rendered = self.render_partial()
        self.assertIn("Kathryn Janeway, profile image", rendered)


class TestLatexMathml(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()

        cls.latex = r"""
            one \[x=2\]
            two $x=2$
            three $$x=2$$
            four \begin{displaymath}x=2\end{displaymath}
            five \begin{equation}x=2\end{equation}
            six \(x=2\)
            seven \begin{math}x=2\end{math}
        """
        setting_handler.save_setting(
            "metadata",
            "latex_mathematics_title_abstract",
            journal=cls.journal,
            value="on",
        )
        cls.maxDiff = None

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_html_allow_block(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        expected = r"""
            one <math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            two <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            three <math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            four <math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            five <math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            six <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            seven <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
        """
        transformed = latex_mathml.to_mathml(
            self.latex,
            self.journal,
            target="html",
            allow_block=True,
        )
        self.assertEqual(transformed, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_html_disallow_block(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        expected = r"""
            one x=2
            two <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            three x=2
            four x=2
            five x=2
            six <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
            seven <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><mi>x</mi><mo>&#x0003D;</mo><mn>2</mn></mrow></math>
        """
        transformed = latex_mathml.to_mathml(
            self.latex,
            self.journal,
            target="html",
            allow_block=False,
        )
        self.assertEqual(transformed, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_xml(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        expected = r"""
            one <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            two <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            three <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            four <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            five <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            six <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
            seven <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:mrow><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mn>2</mml:mn></mml:mrow></mml:math>
        """
        transformed = latex_mathml.to_mathml(
            self.latex,
            self.journal,
            target="xml",
            allow_block=True,
        )
        self.assertEqual(transformed, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_latex_syntax_error(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        value = "some bad latex $${ \over 2}$$"

        # The input should be returned if there is a parsing error,
        # without delimiters to avoid MathJax attempting to parse it.
        # We don't want MathJax touching TeX syntax because we support $...$ and
        # MathJax does not.
        expected = "some bad latex { \over 2}"
        transformed = latex_mathml.to_mathml(value, self.journal)
        self.assertEqual(transformed, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_delimiter_syntax_error(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        value = "bad delimiters $$x=2$ should be left alone"

        # The input should be returned as is if there is a parsing error
        expected = value
        transformed = latex_mathml.to_mathml(value, self.journal)
        self.assertEqual(transformed, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_to_mathml_dollars_left_alone(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)

        # Turn latex parsing off
        setting_handler.save_setting(
            "metadata",
            "latex_mathematics_title_abstract",
            journal=self.journal,
            value="",
        )

        value = "article about $dollars not math just $dollars"
        expected = value
        result = latex_mathml.to_mathml(value, self.journal)
        self.assertEqual(result, expected)

    @patch("core.middleware.GlobalRequestMiddleware.get_current_request")
    def test_strip_delimiters(self, current_request):
        current_request.return_value = helpers.Request(journal=self.journal)
        expected = r"""
            one x=2
            two x=2
            three x=2
            four x=2
            five x=2
            six x=2
            seven x=2
        """
        transformed = latex_mathml.strip_latex_delimiters(
            self.latex,
            self.journal,
        )
        self.assertEqual(transformed, expected)
