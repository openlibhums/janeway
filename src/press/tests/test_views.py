__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import Client, TestCase

from press import views as press_views
from utils.testing import helpers


class PressViewTestsWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()

    def setUp(self):
        self.client = Client()


class URLWithReturnTests(PressViewTestsWithData):

    def test_press_account_links_have_return(self):
        request = helpers.get_request(press=self.press)
        response = press_views.index(request)
        content = response.content.decode()
        self.assertIn('/login/?next=', content)
        self.assertNotIn('"/login/"', content)
        self.assertIn('/register/step/1/?next=', content)
        self.assertNotIn('"/register/step/1/"', content)
