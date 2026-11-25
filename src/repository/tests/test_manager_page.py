from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from repository import logic as repository_logic, models as rm
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
        response = self.get(tab="published")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].paginator.count, 30)
        self.assertEqual(len(response.context["page"].object_list), 25)
        self.assertContains(response, "page=2")

    def test_page_links_keep_the_tab_and_search(self):
        response = self.get(search="Published", tab="published")
        self.assertContains(response, "search=Published&amp;tab=published&amp;page=2")

    def test_opens_on_the_first_tab_with_records(self):
        response = self.get(search="Published")
        self.assertEqual(response.context["active_tab"]["key"], "published")
        counts = {tab["key"]: tab["count"] for tab in response.context["tabs"]}
        self.assertEqual(
            counts, {"new": 0, "accepted": 0, "published": 30, "rejected": 0}
        )

    def test_accepted_and_rejected_have_tabs(self):
        accepted, rejected = rm.Preprint.objects.filter(
            title__startswith="Published"
        ).order_by("pk")[:2]
        rm.Preprint.objects.filter(pk=accepted.pk).update(date_published=None)
        rm.Preprint.objects.filter(pk=rejected.pk).update(
            date_published=None, date_declined=timezone.now()
        )
        counts = {tab["key"]: tab["count"] for tab in self.get().context["tabs"]}
        self.assertEqual(counts["accepted"], 1)
        self.assertEqual(counts["rejected"], 1)
        page = self.get(tab="accepted").context["page"]
        self.assertEqual(list(page.object_list), [accepted])

    def test_search_by_title_or_id(self):
        target = rm.Preprint.objects.get(title="Published number 7")
        for search in ("number 7", str(target.pk)):
            with self.subTest(search):
                page = self.get(search=search).context["page"]
                self.assertIn(target, page.object_list)
        page = self.get(search="no such title").context["page"]
        self.assertEqual(len(page.object_list), 0)

    def test_published_and_unpublished_helpers(self):
        self.client.force_login(self.manager)
        request = self.get().wsgi_request
        published = repository_logic.get_published_preprints(request, [])
        unpublished = repository_logic.get_unpublished_preprints(request, [])
        self.assertEqual(published.count(), 30)
        self.assertFalse(unpublished.filter(date_published__isnull=False).exists())
        self.assertFalse(set(published) & set(unpublished))

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

    def test_search_by_author(self):
        for search in ("Olive Owner", "owner", "frozen_owner@janeway.systems"):
            with self.subTest(search):
                page = self.get(search=search, tab="published").context["page"]
                self.assertEqual(page.paginator.count, 30)
        page = self.get(search="Olive Nobody").context["page"]
        self.assertEqual(page.paginator.count, 0)


@override_settings(URL_CONFIG="domain")
class TestDashboardSearch(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.press.enable_preprints = True
        cls.press.save()
        for title in ("Sea levels", "Mountain soils"):
            helpers.create_preprint(cls.repository, cls.owner, cls.subject, title=title)

    def get(self, **params):
        self.client.force_login(self.owner)
        return self.client.get(
            reverse("repository_dashboard"),
            params,
            SERVER_NAME=self.repository.domain,
        )

    def test_search_by_title_or_id(self):
        target = rm.Preprint.objects.get(title="Sea levels")
        for search in ("sea", str(target.pk)):
            with self.subTest(search):
                preprints = list(self.get(search=search).context["page"])
                self.assertIn(target, preprints)
                self.assertNotIn(
                    rm.Preprint.objects.get(title="Mountain soils"), preprints
                )

    def test_no_match(self):
        response = self.get(search="volcanoes")
        self.assertEqual(len(response.context["page"].object_list), 0)
        self.assertContains(response, "matches “volcanoes”")

    def test_drafts_tab(self):
        draft = helpers.create_preprint(
            self.repository, self.owner, self.subject, title="Half written"
        )
        rm.Preprint.objects.filter(pk=draft.pk).update(
            date_submitted=None, stage=rm.STAGE_PREPRINT_UNSUBMITTED
        )
        response = self.get()
        self.assertEqual(response.context["active_tab"]["key"], "drafts")
        self.assertEqual(list(response.context["page"]), [draft])
        self.assertContains(response, "Continue")
