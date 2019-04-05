from django.test import TestCase, override_settings
from django.utils import translation

from core.models import SettingGroup
from utils.testing import helpers
from utils import setting_handler



class TestSettingHandler(TestCase):

    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.setting_group = SettingGroup.objects.create(name="test_group")

    def test_set_and_get_journal_setting(self):
        setting_name = "test_get_setting"
        setting_value = "banana"
        setting = setting_handler.create_setting(
                "test_group", "test_get_setting",
                type="text",
                pretty_name="Some Name",
                description=None,
        )
        setting_handler.save_setting(
                "test_group", "test_get_setting",
                journal=self.journal_one,
                value=setting_value,
        )
        result = setting_handler.get_setting(
                "test_group", "test_get_setting",
                journal=self.journal_one,
        )
        self.assertEqual(result.value, setting_value)

    def test_get_journal_setting_with_lang_fallback(self):
        setting_name = "test_fallback_setting"
        setting_value = "banana"
        setting = setting_handler.create_setting(
                "test_group", "test_get_setting",
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=True,
        )
        setting_handler.save_setting(
                "test_group", "test_get_setting",
                journal=self.journal_one,
                value=setting_value
        )
        with helpers.activate_translation("es"):
            result = setting_handler.get_setting(
                    "test_group", "test_get_setting",
                    journal=self.journal_one,
                    fallback=True,
            )
        self.assertEqual(result.value, setting_value)

    def test_get_journal_setting_with_default_fallback(self):
        setting_name = "test_get_default_setting"
        setting_value = "default_banana"
        setting = setting_handler.create_setting(
                "test_group", setting_name,
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=False,
        )
        setting_handler.save_setting(
                "test_group", setting_name,
                journal=None,
                value=setting_value,
        )
        result = setting_handler.get_setting(
                "test_group", setting_name,
                journal=self.journal_one,
                fallback=True,
        )
        self.assertEqual(result.value, setting_value)

    def test_get_journal_setting_with_lang_and_default_fallback(self):
        setting_name = "test_get_default_fallback_for_lang_setting"
        setting_value = "banana"
        setting = setting_handler.create_setting(
                "test_group", setting_name,
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=True,
        )
        setting_handler.save_setting(
                "test_group", setting_name,
                journal=None,
                value=setting_value
        )
        with helpers.activate_translation("es"):
            result = setting_handler.get_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
                    fallback=True,
            )
        self.assertEqual(result.value, setting_value)

    @helpers.activate_translation("es")
    def test_get_journal_setting_with_language(self):
        setting_name = "test_get_setting_with_language"
        setting_value = "plátano"
        setting = setting_handler.create_setting(
                "test_group", setting_name,
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=True,
        )
        setting_handler.save_setting(
                "test_group", setting_name,
                journal=self.journal_one,
                value=setting_value,
        )
        result = setting_handler.get_setting(
                "test_group", setting_name,
                journal=self.journal_one,
        )
        self.assertEqual(result.value, setting_value)

