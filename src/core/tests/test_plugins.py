from collections import namedtuple

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from core import plugin_loader
from utils.models import Version

MockSettings = namedtuple("MockSettings", ["JANEWAY_VERSION", "PLUGIN_NAME"])
MockSettingsNoVersion = namedtuple("MockSettings", ["PLUGIN_NAME"])

class TestPluginLoader(TestCase):

    def setUp(self):
        Version.objects.create(number="9.6.3")

    def test_plugin_version_is_valid(self):
        mock_settings = MockSettings(
            PLUGIN_NAME="Mock Plugin",
            JANEWAY_VERSION="1.3.6"
        )

        plugin_loader.validate_plugin_version(mock_settings)

    def test_plugin_version_is_not_valid(self):
        mock_settings = MockSettings(
            PLUGIN_NAME="Mock Plugin",
            JANEWAY_VERSION="10.7.2"
        )

        with self.assertRaises(ImproperlyConfigured):
            plugin_loader.validate_plugin_version(mock_settings)

    def test_plugin_minor_version_is_not_valid(self):
        mock_settings = MockSettings(
            PLUGIN_NAME="Mock Plugin",
            JANEWAY_VERSION="10.6.8"
        )

        with self.assertRaises(ImproperlyConfigured):
            plugin_loader.validate_plugin_version(mock_settings)

    def test_unpinned_plugin_version_is_valid(self):
        mock_settings = MockSettingsNoVersion(
            PLUGIN_NAME="Mock Plugin",
        )

        plugin_loader.validate_plugin_version(mock_settings)
