from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from freezegun import freeze_time

from api import serializers as api_serializers
from repository import logic as repository_logic, models as rm
from submission import models as sm
from repository.tests.test_file_access import PDF, FileAccessTestBase


@freeze_time("2026-11-11 12:00:00")
class FundingTests(FileAccessTestBase):
    """Funding on every repository, reusing the journals' ArticleFunding."""

    def setUp(self):
        super().setUp()
        # Funding is for every repository, not only institutional ones.
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        self.preprint, self.file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        sm.FrozenAuthor.objects.create(
            preprint=self.preprint, first_name="Ada", last_name="Author", order=0
        )
        self.ukri = sm.ArticleFunding.objects.create(
            preprint=self.preprint,
            name="UK Research and Innovation",
            fundref_id="https://doi.org/10.13039/100014013",
            funding_id="EP/X000001/1",
        )

    def post(self, url, data, user):
        self.client.force_login(user)
        return self.client.post(
            url, data, SERVER_NAME=self.repository.domain, HTTP_HX_REQUEST="true"
        )

    def record_url(self):
        return reverse(
            "repository_preprint_funding", kwargs={"preprint_id": self.preprint.pk}
        )

    # The model

    def test_an_entry_has_at_most_one_owner(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            sm.ArticleFunding.objects.create(
                name="Two owners",
                preprint=self.preprint,
                preprint_version=self.preprint.current_version,
            )
        # Journal funding without an article, as old data may have, is fine.
        sm.ArticleFunding.objects.create(name="No owner")

    # Editing

    def test_a_depositor_adds_funding_while_submitting(self):
        draft = rm.Preprint.objects.create(
            repository=self.repository, owner=self.owner, title="A draft"
        )
        page = self.client
        page.force_login(self.owner)
        response = page.get(
            reverse("repository_authors", kwargs={"preprint_id": draft.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(response, "data-funding-editor")
        url = reverse("repository_preprint_funding", kwargs={"preprint_id": draft.pk})
        response = self.post(
            url,
            {
                "action": "add",
                "funding-add-name": "Wellcome Trust",
                "funding-add-funding_id": "226789/Z/22/Z",
            },
            self.owner,
        )
        self.assertNotContains(response, "<html")
        self.assertContains(response, "Wellcome Trust")
        entry = draft.funding.get()
        prefix = "funding-{}".format(entry.pk)
        self.post(
            url,
            {
                "action": "edit",
                "entry": entry.pk,
                prefix + "-name": "Wellcome",
                prefix + "-funding_id": "1",
            },
            self.owner,
        )
        entry.refresh_from_db()
        self.assertEqual(entry.name, "Wellcome")
        self.post(url, {"action": "remove", "entry": entry.pk}, self.owner)
        self.assertFalse(draft.funding.exists())

    def test_after_submission_only_moderators_edit_it_directly(self):
        response = self.post(
            self.record_url(), {"action": "remove", "entry": self.ukri.pk}, self.owner
        )
        self.assertEqual(response.status_code, 404)
        self.post(
            self.record_url(), {"action": "remove", "entry": self.ukri.pk}, self.manager
        )
        self.assertFalse(self.preprint.funding.exists())

    def test_the_manager_page_has_the_editor(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse(
                "repository_manager_article", kwargs={"preprint_id": self.preprint.pk}
            ),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(response, "data-funding-editor")
        self.assertContains(response, "UK Research and Innovation")

    # Updates and versions

    def test_funding_goes_through_updates_and_versions_keep_theirs(self):
        update, _error = repository_logic.start_update(
            self.preprint, "metadata_correction"
        )
        self.assertEqual(
            [e.name for e in update.funding], ["UK Research and Innovation"]
        )
        url = reverse(
            "repository_update_funding",
            kwargs={"preprint_id": self.preprint.pk, "update_id": update.pk},
        )
        self.post(
            url, {"action": "add", "funding-add-name": "Leverhulme Trust"}, self.owner
        )
        self.assertEqual(self.preprint.funding.count(), 1)  # not live yet

        self.assertIsNone(repository_logic.submit_update(update))
        update.refresh_from_db()
        self.assertTrue(update.funding_changed)
        self.assertFalse(update.changes_only_additional_files)
        removed, added = update.funding_changes()
        self.assertEqual([e.name for e in added], ["Leverhulme Trust"])

        first = self.preprint.current_version
        self.assertTrue(update.approve())
        self.assertEqual(
            sorted(self.preprint.funding.values_list("name", flat=True)),
            ["Leverhulme Trust", "UK Research and Innovation"],
        )
        self.assertEqual(self.preprint.current_version.version, first.version + 1)
        first.refresh_from_db()
        self.assertEqual(
            [e.name for e in first.funding], ["UK Research and Innovation"]
        )

    # Where it shows

    def test_the_record_page_lists_funding_in_every_theme(self):
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(self.preprint.local_url)
                self.assertContains(response, "Funding")
                self.assertContains(response, "UK Research and Innovation")
                self.assertContains(response, "EP/X000001/1")

    def test_crossref_jats_rioxx_and_the_api_carry_it(self):
        crossref = render_to_string(
            "common/identifiers/crossref_preprint.xml",
            {"version": self.preprint.current_version},
        )
        self.assertIn(
            '<assertion name="funder_name">UK Research and Innovation</assertion>',
            crossref,
        )
        self.assertIn(
            '<assertion name="award_number">EP/X000001/1</assertion>', crossref
        )

        identifier = "oai:{}:id:{}".format(self.repository.short_name, self.preprint.pk)
        jats = self.client.get(
            "{}?{}".format(
                reverse("OAI_list_records"),
                urlencode(
                    {
                        "verb": "GetRecord",
                        "metadataPrefix": "jats",
                        "identifier": identifier,
                    }
                ),
            ),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(
            jats, "<funding-source>UK Research and Innovation</funding-source>"
        )

        self.repository.repository_type = rm.Repository.TYPE_INSTITUTIONAL
        self.repository.save()
        rioxx = self.client.get(
            "{}?{}".format(
                reverse("OAI_list_records"),
                urlencode(
                    {
                        "verb": "GetRecord",
                        "metadataPrefix": "rioxx",
                        "identifier": identifier,
                    }
                ),
            ),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(rioxx, 'funder_name="UK Research and Innovation"')

        data = api_serializers.PreprintSerializer(self.preprint).data
        self.assertEqual(
            data["funding"],
            [
                {
                    "funder": "UK Research and Innovation",
                    "funder_id": "https://doi.org/10.13039/100014013",
                    "grant": "EP/X000001/1",
                    "statement": None,
                }
            ],
        )
