from django.conf import settings
from django.test import TestCase, override_settings

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
        with helpers.activate_translation("cy"):
            result = setting_handler.get_setting(
                    "test_group", "test_get_setting",
                    journal=self.journal_one,
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
        with helpers.activate_translation("cy"):
            result = setting_handler.get_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
            )
        self.assertEqual(result.value, setting_value)

    @helpers.activate_translation("cy")
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

    def test_save_setting(self):
        setting_name = "test_save_setting"
        setting_value = "This is the setting"
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

    @override_settings(USE_I18N=True)
    @helpers.activate_translation("cy")
    def test_save_translated_setting_without_default_lang(self):
        setting_name = "test_save_translated_setting_without_default_lang"
        setting_value = "plátano"
        expected_result = None
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
        with helpers.activate_translation(settings.LANGUAGE_CODE):
            result = setting_handler.get_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
            )
        self.assertEqual(result.value, expected_result)

    @override_settings(USE_I18N=True)
    def test_save_translated_setting_with_default_lang(self):
        setting_name = "test_save_translated_setting_with_default_lang"
        setting_value = "banana"
        xl_setting_value = "plátano"
        setting = setting_handler.create_setting(
                "test_group", setting_name,
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=True,
        )
        #Save the setting on the default language
        setting_handler.save_setting(
                "test_group", setting_name,
                journal=self.journal_one,
                value=setting_value,
        )
        #Save the translated value
        with helpers.activate_translation("cy"):
            setting_handler.save_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
                    value=xl_setting_value,
            )
        result = setting_handler.get_setting(
                "test_group", setting_name,
                journal=self.journal_one,
        ).value
        with helpers.activate_translation("cy"):
            xl_result = setting_handler.get_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
            ).value

        self.assertEqual(result, setting_value)
        self.assertEqual(xl_result, xl_setting_value)

    @override_settings(USE_I18N=True)
    def test_update_translated_setting_with_default_lang(self):
        setting_name = "test_update_translated_setting_with_default_lang"
        setting_value = "banana"
        xl_setting_value = "plátano"
        setting = setting_handler.create_setting(
                "test_group", setting_name,
                type="text",
                pretty_name="Pretty Name",
                description=None,
                is_translatable=True,
        )
        #Save the setting on the default language
        setting_handler.save_setting(
                "test_group", setting_name,
                journal=self.journal_one,
                value=setting_value,
        )
        #Save  a wrongly translated value
        wrong_translation = xl_setting_value + "mal"
        with helpers.activate_translation("cy"):
            setting_handler.save_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
                    value=wrong_translation,
            )
            #save the correctly translated value
            setting_handler.save_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
                    value=xl_setting_value,
            )

        #Fetch the results
        result = setting_handler.get_setting(
                "test_group", setting_name,
                journal=self.journal_one,
        ).value
        with helpers.activate_translation("cy"):
            xl_result = setting_handler.get_setting(
                    "test_group", setting_name,
                    journal=self.journal_one,
            ).value

        self.assertEqual(result, setting_value)
        self.assertEqual(xl_result, xl_setting_value)
