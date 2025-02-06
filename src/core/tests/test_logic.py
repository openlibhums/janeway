__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import uuid
from mock import patch

from django.test import TestCase

from core import logic
from utils.testing import helpers

class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = helpers.Request()
        cls.request.press = cls.press
        cls.request.journal = cls.journal_one
        cls.request.site_type = cls.journal_one
        cls.request.GET = {}
        cls.request.POST = {}
        cls.inactive_user = helpers.create_user('zlwdi6frbtlh4gditdir@example.org')
        cls.inactive_user.is_active = False
        cls.inactive_user.confirmation_code = '8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55'
        cls.inactive_user.clean()
        cls.inactive_user.save()

        # The result of passing a URL through the |urlencode template filter
        cls.next_url_encoded = '/target/page/%3Fq%3Da'

    def test_render_nested_settings(self):
        expected_rendered_setting = "<p>For help with Janeway, contact <a href=\"mailto:--No support email set--\">--No support email set--</a>.</p>"
        rendered_setting = logic.render_nested_setting(
            'support_contact_message_for_staff',
            'general',
            self.request,
            nested_settings=[('support_email','general')],
        )
        self.assertEqual(expected_rendered_setting, rendered_setting)

    @patch('core.logic.reverse')
    def test_reverse_with_next_in_get_request(self, mock_reverse):
        mock_reverse.return_value = '/my/path/?my=params'
        self.request.GET = {'next': self.next_url_encoded}
        reversed_url = logic.reverse_with_next('/test/', self.request)
        self.assertIn(self.next_url_encoded, reversed_url)

    @patch('core.logic.reverse')
    def test_reverse_with_next_in_post_request(self, mock_reverse):
        mock_reverse.return_value = '/my/path/?my=params'
        self.request.POST = {'next': self.next_url_encoded}
        reversed_url = logic.reverse_with_next('/test/', self.request)
        self.assertIn(self.next_url_encoded, reversed_url)

    @patch('core.logic.reverse')
    def test_reverse_with_next_in_kwarg(self, mock_reverse):
        mock_reverse.return_value = '/my/path/?my=params'
        reversed_url = logic.reverse_with_next(
            '/test/',
            self.request,
            next_url=self.next_url_encoded,
        )
        self.assertIn(self.next_url_encoded, reversed_url)

    @patch('core.logic.reverse')
    def test_reverse_with_next_no_next(self, mock_reverse):
        mock_reverse.return_value = '/my/url/?my=params'
        reversed_url = logic.reverse_with_next('/test/', self.request)
        self.assertEqual(mock_reverse.return_value, reversed_url)

    def test_get_confirm_account_url(self):
        url = logic.get_confirm_account_url(
            self.request,
            self.inactive_user,
            next_url=self.next_url_encoded,
        )
        self.assertIn(
            f'/register/step/2/8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55/?next={ self.next_url_encoded }',
            url,
        )
