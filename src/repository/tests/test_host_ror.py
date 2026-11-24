from django.test import override_settings
from django.urls import reverse

from core import models as core_models
from repository import forms
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase


def ror_organization(ror_id, name):
    organization = core_models.Organization.objects.create(ror_id=ror_id)
    core_models.OrganizationName.objects.create(
        value=name,
        ror_display_for=organization,
        label_for=organization,
    )
    return organization


@override_settings(URL_CONFIG="domain")
class TestHostRorId(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.host = ror_organization("02mb95055", "Birkbeck, University of London")
        cls.other = ror_organization("02jx3x895", "University College London")

    def setUp(self):
        self.preprint.date_submitted = None
        self.preprint.save()
        self.author = self.preprint.frozen_authors().get(author=self.owner)

    def search(self, q=""):
        self.client.force_login(self.owner)
        return self.client.get(
            reverse(
                "repository_organization_search",
                args=[self.preprint.pk, self.author.pk],
            ),
            {"q": q} if q else {},
            SERVER_NAME=self.repository.domain,
        )

    def test_host_institution_is_listed_first_once(self):
        self.repository.host_ror_id = self.host.ror_id
        self.repository.save()
        response = self.search("London")
        self.assertEqual(response.context["host_organization"], self.host)
        self.assertNotIn(self.host, response.context["organization_list"])
        content = response.content.decode()
        self.assertLess(
            content.index("Birkbeck, University of London"),
            content.index("University College London"),
        )

    def test_host_institution_is_shown_whatever_the_search(self):
        self.repository.host_ror_id = self.host.ror_id
        self.repository.save()
        self.assertContains(self.search("College"), "Birkbeck, University of London")

    def test_nothing_is_pinned_without_the_setting(self):
        response = self.search("London")
        self.assertIsNone(response.context["host_organization"])
        self.assertNotContains(response, "Host institution")

    def form(self, value):
        data = forms.RepositorySubmission(
            instance=self.repository, press=self.press
        ).initial
        data["host_ror_id"] = value
        return forms.RepositorySubmission(
            data, instance=self.repository, press=self.press
        )

    def test_settings_take_a_ror_link_or_id(self):
        for value in ("https://ror.org/02mb95055", "02mb95055"):
            with self.subTest(value):
                form = self.form(value)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["host_ror_id"], "02mb95055")

    def test_settings_reject_unknown_or_bad_ror_ids(self):
        self.assertIn("host_ror_id", self.form("05xg72x27").errors)
        self.assertIn("host_ror_id", self.form("not-a-ror").errors)

    def test_submission_details_no_longer_edit_people(self):
        form = forms.RepositorySubmission(instance=self.repository, press=self.press)
        self.assertNotIn("managers", form.fields)
        self.assertNotIn("moderators", form.fields)
