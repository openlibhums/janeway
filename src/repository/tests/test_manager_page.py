from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from repository import models as rm
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class TestManagerPage(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.press.enable_preprints = True
        cls.press.save()
        cls.submission_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.repository,
            name="Article",
            name_plural="Articles",
            slug="article",
        )
        for number in range(30):
            preprint = helpers.create_preprint(
                cls.repository,
                cls.owner,
                cls.subject,
                title=f"Published number {number}",
            )
            preprint.date_published = timezone.now()
            preprint.date_accepted = timezone.now()
            preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
            preprint.submission_type = cls.submission_type
            preprint.save()

    def get(self, **params):
        self.client.force_login(self.manager)
        return self.client.get(
            reverse("preprints_manager"),
            params,
            SERVER_NAME=self.repository.domain,
        )

    def test_published_preprints_are_paged(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["published_count"], 30)
        self.assertEqual(len(response.context["published_page"].object_list), 25)
        self.assertContains(response, "published_page=2")

    def test_page_links_keep_the_other_list_and_search(self):
        response = self.get(q="Published", unpublished_page="1")
        self.assertContains(response, "published_page=2")
        self.assertContains(response, "q=Published")
        self.assertContains(response, "unpublished_page=1")

    def test_search_by_title_or_id(self):
        target = rm.Preprint.objects.get(title="Published number 7")
        for search in ("number 7", str(target.pk)):
            with self.subTest(search):
                page = self.get(q=search).context["published_page"]
                self.assertIn(target, page.object_list)
        page = self.get(q="no such title").context["published_page"]
        self.assertEqual(len(page.object_list), 0)

    def page_queries(self):
        """The page's repository queries; session and login ones vary."""
        with CaptureQueriesContext(connection) as queries:
            self.get()
        return len([q for q in queries.captured_queries if '"repository_' in q["sql"]])

    def add_unpublished(self, numbers):
        for number in numbers:
            preprint = helpers.create_preprint(
                self.repository,
                self.owner,
                self.subject,
                title=f"Unpublished number {number}",
            )
            preprint.submission_type = self.submission_type
            preprint.save()

    def test_queries_do_not_grow_with_the_number_of_preprints(self):
        self.add_unpublished(range(30, 32))
        before = self.page_queries()
        self.add_unpublished(range(32, 42))
        self.assertEqual(self.page_queries(), before)
