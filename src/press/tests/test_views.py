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


class URLWithReturnTests(PressViewTestsWithData):

    @override_settings(URL_CONFIG='path')
    def test_press_nav_account_links_do_not_have_return(self):
        """
        Check that the url_with_return tag has *not* been used
        in the site nav links for login and registration.
        """
        request = helpers.get_request(press=self.press)
        response = press_views.index(request)
        content = response.content.decode()
        self.assertNotIn('/login/?next=', content)
        self.assertNotIn('/register/step/1/?next=', content)
