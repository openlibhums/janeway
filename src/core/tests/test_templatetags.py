
from utils.testing import helpers
from django.test import TestCase, override_settings
from core.templatetags import fqdn

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
