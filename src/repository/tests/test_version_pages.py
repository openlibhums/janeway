from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from repository import logic as repository_logic, models as rm
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase
from submission import models as sm


@override_settings(URL_CONFIG="domain")
class TestVersionPages(PreprintFrozenAuthorTestBase):
    def get(self, url):
        return self.client.get(url, SERVER_NAME=self.repository.domain)

    def version_url(self, number):
        return reverse("repository_preprint_version", args=[self.preprint.pk, number])

    def test_each_version_has_its_own_page(self):
        self.preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
        self.preprint.date_published = timezone.now()
        self.preprint.save()
        sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        update, _error = repository_logic.start_update(
            self.preprint,
            "metadata_correction",
        )
        update.title = "A corrected title"
        update.save()
        update.authors.get(author=self.owner).delete()
        self.assertIsNone(repository_logic.submit_update(update))
        update.approve()

        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(self.version_url(1))
                self.assertContains(response, "This is a Test Preprint")
                self.assertContains(response, "Olive Owner")
                self.assertContains(response, "older-version-notice")
                self.assertNotContains(response, "A corrected title")

        self.assertRedirects(
            self.get(self.version_url(2)),
            self.preprint.local_url,
            fetch_redirect_response=False,
        )
        response = self.get(self.preprint.local_url)
        self.assertContains(response, "A corrected title")
        self.assertNotContains(response, "Olive Owner")
        self.assertContains(response, f'href="{self.version_url(1)}"')
        self.assertEqual(self.get(self.version_url(3)).status_code, 404)
