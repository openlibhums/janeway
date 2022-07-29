from django.test import TestCase

from core import logic
from core.models import SettingGroup
from utils.testing import helpers

class TestLogic(TestCase):
    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.request = helpers.Request()
        self.request.press = self.press
        self.request.journal = self.journal_one
        self.request.site_type = self.journal_one

    def test_render_nested_settings(self):
        expected_rendered_setting = "<p>For help with Janeway, contact <a href=\"mailto:--No support email set--\">--No support email set--</a>.</p>"
        rendered_setting = logic.render_nested_setting(
            'support_contact_message_for_staff',
            'general',
            self.request,
            nested_settings=[('support_email','general')],
        )
        self.assertEqual(expected_rendered_setting, rendered_setting)
