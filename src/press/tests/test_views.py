__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import Client, TestCase, override_settings

from press import views as press_views
from utils.testing import helpers


class PressViewTestsWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.press_manager = helpers.create_user(
            username='rcuaekqhrswerhrttydo@example.org',
        )
        cls.press_manager.is_active = True
        cls.press_manager.is_staff = True
        cls.press_manager.save()


class URLWithReturnTests(PressViewTestsWithData):

    @override_settings(URL_CONFIG='domain')
    def test_press_nav_account_links_do_not_have_return(self):
        """
        Check that the url_with_return tag has *not* been used
        in the site nav links for login and registration.
        """
        response = self.client.get(
            '/',
            SERVER_NAME=self.press.domain,
        )
        content = response.content.decode()
        self.assertNotIn('/login/?next=', content)
        self.assertNotIn('/register/step/1/?next=', content)
