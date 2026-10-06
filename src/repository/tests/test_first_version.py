from django.test import TestCase, override_settings
from django.urls import reverse

from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class TestFirstVersion(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_roles(["author"])
        cls.press = helpers.create_press()
        cls.manager = helpers.create_user("manager@example.org")
        cls.manager.is_active = True
        cls.manager.save()
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.manager],
            [],
        )
        cls.owner = helpers.create_user("owner@example.org")

    def test_accepting_makes_the_submitted_file_version_1(self):
        preprint = helpers.create_preprint(self.repository, self.owner, self.subject)
        preprint.save()
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_manager_article", args=[preprint.pk]),
            {"accept": "", "datetime": "2026-10-01 10:00", "timezone": "UTC"},
            SERVER_NAME=self.repository.domain,
        )
        preprint.refresh_from_db()
        self.assertTrue(preprint.date_accepted)
        self.assertEqual(preprint.current_version.version, 1)
        self.assertEqual(preprint.current_version.file, preprint.submission_file)
