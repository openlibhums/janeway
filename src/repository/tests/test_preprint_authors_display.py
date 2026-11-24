from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from repository import models as rm
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase


@override_settings(URL_CONFIG="domain")
class TestPreprintAuthorsDisplay(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.now()
        cls.preprint.save()
        organization = core_models.Organization.objects.create(ror_id="02mb95055")
        core_models.OrganizationName.objects.create(
            value="Birkbeck, University of London",
            ror_display_for=organization,
            label_for=organization,
        )
        author = cls.preprint.frozen_authors().get(author=cls.owner)
        author.affiliations.delete()
        core_models.ControlledAffiliation.objects.create(
            frozen_author=author,
            organization=organization,
            is_primary=True,
        )

    def test_affiliation_and_ror_link_on_every_theme(self):
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.client.get(
                    reverse("repository_preprint", args=[self.preprint.pk]),
                    SERVER_NAME=self.repository.domain,
                )
                self.assertContains(response, "Olive Owner")
                self.assertContains(response, "Birkbeck, University of London")
                self.assertContains(response, 'href="https://ror.org/02mb95055"')
                self.assertContains(response, "View ROR record for")
