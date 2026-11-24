from django.test import override_settings
from django.urls import reverse

from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase
from submission import models as submission_models
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class TestRepositoryLicences(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.press.enable_preprints = True
        cls.press.save()
        cls.used = submission_models.Licence.objects.create(
            press=cls.press, name="Used licence", short_name="USED", url="https://u.org"
        )
        cls.unused = submission_models.Licence.objects.create(
            press=cls.press,
            name="Spare licence",
            short_name="SPARE",
            url="https://s.org",
        )
        cls.preprint.license = cls.used
        cls.preprint.save()

    def request(self, name, args=None, data=None):
        self.client.force_login(self.manager)
        method = self.client.post if data is not None else self.client.get
        return method(
            reverse(name, args=args),
            data or {},
            SERVER_NAME=self.repository.domain,
        )

    def test_lists_press_licences_with_use(self):
        response = self.request("repository_licenses")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Used licence")
        self.assertContains(response, "Spare licence")

    def test_add_a_licence_and_offer_it(self):
        self.request(
            "repository_licenses",
            data={
                "save_licence": "",
                "name": "New licence",
                "short_name": "NEW",
                "url": "https://n.org",
                "order": 0,
                "available_for_submission": "on",
            },
        )
        licence = submission_models.Licence.objects.get(short_name="NEW")
        self.assertEqual(licence.press, self.press)
        self.assertIn(licence, self.repository.active_licenses.all())

    def test_edit_a_licence(self):
        self.request(
            "repository_license_edit",
            args=[self.unused.pk],
            data={
                "save_licence": "",
                "name": "Renamed",
                "short_name": "SPARE",
                "url": "https://s.org",
                "order": 0,
            },
        )
        self.unused.refresh_from_db()
        self.assertEqual(self.unused.name, "Renamed")

    def test_choose_offered_licences(self):
        self.request(
            "repository_licenses",
            data={"save_active": "", "active_licenses": [self.unused.pk]},
        )
        self.assertEqual(list(self.repository.active_licenses.all()), [self.unused])

    def test_delete_only_unused_licences(self):
        self.request("repository_license_delete", [self.used.pk], {"delete": ""})
        self.assertTrue(submission_models.Licence.objects.filter(pk=self.used.pk))
        self.request("repository_license_delete", [self.unused.pk], {"delete": ""})
        self.assertFalse(submission_models.Licence.objects.filter(pk=self.unused.pk))

    def test_journal_licences_are_not_editable_here(self):
        journal_licence = submission_models.Licence.objects.create(
            journal=self.journal, name="Journal", short_name="J", url="https://j.org"
        )
        response = self.request("repository_license_edit", [journal_licence.pk])
        self.assertEqual(response.status_code, 404)

    def test_moderators_cannot_manage_licences(self):
        moderator = helpers.create_user("lic_mod@janeway.systems")
        moderator.is_active = True
        moderator.save()
        self.repository.moderators.add(moderator)
        self.client.force_login(moderator)
        response = self.client.get(
            reverse("repository_licenses"), SERVER_NAME=self.repository.domain
        )
        self.assertEqual(response.status_code, 403)
