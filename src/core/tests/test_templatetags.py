
from utils.testing import helpers
from django.test import TestCase, override_settings, RequestFactory
from core.templatetags import fqdn, dates
from datetime import datetime
from django.utils.translation import activate
from django.conf import settings

class TestFqdn(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.journal_two.domain = None
        cls.journal_two.save()

    def test_stateless_site_url_for_press(self):
        url_name = 'press_all_users' 
        url = fqdn.stateless_site_url(self.press, url_name)
        self.assertEqual(url, 'http://localhost/press/user/all/')

    @override_settings(URL_CONFIG="domain")
    def test_stateless_site_url_for_journal_domain(self):
        url_name = 'journal_users' 
        url = fqdn.stateless_site_url(self.journal_one, url_name)
        self.assertEqual(url, f'http://{self.journal_one.domain}/user/all/')

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_for_journal_path(self):
        url_name = 'journal_users' 
        url = fqdn.stateless_site_url(self.journal_two, url_name)
        self.assertEqual(url, f'http://{self.journal_two.press.domain}/{self.journal_two.code}/user/all/')

class TestDateHuman(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_dates = {
            'date':         datetime(2023, 12, 3),  # 3 December 2023
            'leap_year':    datetime(2024, 2, 29),  # 29 February 2024
            'new_year':     datetime(2021, 1, 1),  # 1 January 2021 
        }
        cls.expected_formats = {
            'date': {
                'en': "3 December 2023",
                'en-us': "3 December 2023",
                'fr': "3 décembre 2023",
                'de': "3 Dezember 2023",
                'nl': "3 december 2023",
                'cy': "3 Rhagfyr 2023",
                'es': "3 diciembre 2023",
            },
            'leap_year': {
                'en': "29 February 2024",
                'en-us': "29 February 2024",
                'fr': "29 février 2024",
                'de': "29 Februar 2024",
                'nl': "29 februari 2024",
                'cy': "29 Chwefror 2024",
                'es': "29 febrero 2024",
            },
            'new_year': {
                'en': "1 January 2021",
                'en-us': "1 January 2021",
                'fr': "1 janvier 2021",
                'de': "1 Januar 2021",
                'nl': "1 januari 2021",
                'cy': "1 Ionawr 2021",
                'es': "1 enero 2021",
            },
        }

    def test_non_dates(self):
        """Test date_human hides non-dates from user to ensure incorrect information is not displayed."""
        test_non_dates = {
            'string':               "2023,12,3",                    # string
            'int':                  134567,                         # integer
            'zero':                 0,                              # zero
        }
        for key, test_non_date in test_non_dates.items():
            with self.subTest(non_date=key):
                result = dates.date_human(test_non_date)
                # When given a non-date, the tag should hide that content from the user by returning an empty string
                self.assertIsInstance(result, str,
                    f"Failed for non-existent date '{key}'. Expected string, got '{type(result)}'."                  
                )
                self.assertEqual(result, "",
                    f"Failed for non-existent date '{key}'. Expected empty string, got '{type(result)}'."                   
                )

    def test_date_human_all_languages(self):
        """Test date_human with all supported languages from settings"""
        for key, test_date in self.test_dates.items(): 
            for lang_code, language in settings.LANGUAGES:
                with self.subTest(date=key, code=lang_code):
                    activate(lang_code)
                    result = dates.date_human(test_date)
                    expected = self.expected_formats[key].get(lang_code)
                    self.assertEqual(result, expected, 
                        f"Failed for {lang_code}:{language}.  Expected '{expected}', actual '{result}'."
                    )
    
    def test_date_human_browser_languages(self):
        """Test data_human uses application language regardless of browser language setting"""
        supported_languages = [lang[0] for lang in settings.LANGUAGES]
        
        non_supported_languages = ['ja','en-nz','es-ni','ar-sa']

        for lang in non_supported_languages:
            self.assertNotIn(lang, supported_languages,
                f"Test needs updating. Sample non-supported language '{lang}' is now supported."         
            )

        browser_languages = supported_languages + non_supported_languages
        
        factory = RequestFactory()
        def set_browser_lang(lang_code):
            request = factory.get('/')
            request.META['HTTP_ACCEPT_LANGUAGE'] = lang_code

        for lang in browser_languages:
            set_browser_lang(lang)
            self.test_date_human_all_languages()