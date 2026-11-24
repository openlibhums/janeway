import datetime
import importlib
from xml.etree import ElementTree as ET

from django.apps import apps
from django.urls import reverse
from django.utils.http import urlencode
from freezegun import freeze_time

from repository import logic as repository_logic, models as rm
from submission import models as sm
from repository.tests.test_file_access import PDF, FileAccessTestBase

NS = {
    "rioxx": "http://www.rioxx.net/schema/v3.0/rioxx/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "rioxxterms": "http://www.rioxx.net/schema/v3.0/rioxxterms/",
}


@freeze_time("2026-11-11 12:00:00")
class PublicationDetailsTests(FileAccessTestBase):
    def setUp(self):
        super().setUp()
        self.preprint, self.file = self.published_preprint(
            PDF, "aam.pdf", "application/pdf"
        )
        sm.FrozenAuthor.objects.create(
            preprint=self.preprint, first_name="Ada", last_name="Author", order=0
        )
        self.details = rm.PublicationDetails.objects.create(
            preprint=self.preprint,
            venue_title="Proceedings of the Royal Society B",
            volume="291",
            issue="2014",
            pages="1-12",
            publisher="Royal Society",
            issn="0962-8452",
            accepted_date=datetime.date(2024, 1, 10),
            publication_date=datetime.date(2024, 3, 1),
            publication_status="published",
            oa_type="green",
        )

    def post(self, url, data, user):
        self.client.force_login(user)
        return self.client.post(
            url, data, SERVER_NAME=self.repository.domain, HTTP_HX_REQUEST="true"
        )

    def test_venue_line(self):
        self.assertEqual(
            self.details.venue_line,
            "Proceedings of the Royal Society B, 291(2014), 1-12",
        )

    def test_the_depositor_gives_them_on_the_details_step(self):
        self.client.force_login(self.owner)
        draft = rm.Preprint.objects.create(
            repository=self.repository,
            owner=self.owner,
            title="A draft",
            submission_type=rm.RepositorySubmissionType.objects.create(
                repository=self.repository,
                name="Article",
                name_plural="Articles",
                slug="article",
            ),
        )
        page = self.client.get(
            reverse("repository_submit_with_id", kwargs={"preprint_id": draft.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(page, "data-publication-details")
        self.assertContains(page, 'name="pub-accepted_date"')
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        page = self.client.get(
            reverse("repository_submit_with_id", kwargs={"preprint_id": draft.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertNotContains(page, 'name="pub-accepted_date"')

    def test_moderators_edit_them_in_place(self):
        url = reverse(
            "repository_preprint_publication_details",
            kwargs={"preprint_id": self.preprint.pk},
        )
        response = self.post(
            url, {"pub-venue_title": "Nature", "pub-oa_type": "gold"}, self.manager
        )
        self.assertNotContains(response, "<html")
        self.assertContains(response, "Saved.")
        self.details.refresh_from_db()
        self.assertEqual(
            (self.details.venue_title, self.details.oa_type), ("Nature", "gold")
        )
        # Authors change them through an update, not directly.
        self.assertEqual(
            self.post(url, {"pub-venue_title": "X"}, self.owner).status_code, 403
        )

    def test_they_go_through_updates_and_versions_keep_theirs(self):
        update, _error = repository_logic.start_update(
            self.preprint, "metadata_correction"
        )
        self.assertEqual(
            update.publication_details.venue_title, "Proceedings of the Royal Society B"
        )
        url = reverse(
            "repository_update_publication_details",
            kwargs={"preprint_id": self.preprint.pk, "update_id": update.pk},
        )
        data = {
            "pub-" + name: getattr(self.details, name) or ""
            for name in rm.PublicationDetails.DETAIL_FIELDS
        }
        data["pub-publication_status"] = "published"
        data["pub-volume"] = "292"
        self.post(url, data, self.owner)
        self.assertIsNone(repository_logic.submit_update(update))
        update.refresh_from_db()
        self.assertTrue(update.publication_details_changed)
        self.assertEqual(
            [
                (str(name), old, new)
                for name, old, new in update.publication_details_changes()
            ],
            [("volume", "291", "292")],
        )
        first = self.preprint.current_version
        self.assertTrue(update.approve())
        self.assertEqual(self.preprint.publication_details.volume, "292")
        first.refresh_from_db()
        self.assertEqual(first.publication_details.volume, "291")

    def test_the_record_page_and_rioxx_show_them(self):
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(self.preprint.local_url)
                self.assertContains(
                    response, 'class="no-bullet list-no-bullet publication-details"'
                )
                self.assertContains(
                    response, "Proceedings of the Royal Society B, 291(2014), 1-12"
                )
        response = self.client.get(
            "{}?{}".format(
                reverse("OAI_list_records"),
                urlencode(
                    {
                        "verb": "GetRecord",
                        "metadataPrefix": "rioxx",
                        "identifier": "oai:{}:id:{}".format(
                            self.repository.short_name, self.preprint.pk
                        ),
                    }
                ),
            ),
            SERVER_NAME=self.repository.domain,
        )
        rioxx = ET.fromstring(response.content).find(".//rioxx:rioxx", NS)
        self.assertEqual(rioxx.find("dcterms:dateAccepted", NS).text, "2024-01-10")
        self.assertEqual(
            rioxx.find("rioxxterms:publication_date", NS).text, "2024-03-01"
        )
        self.assertEqual(rioxx.find("dc:publisher", NS).text, "Royal Society")
        self.assertEqual(rioxx.find("dc:source", NS).text, "0962-8452")
        self.assertIsNotNone(rioxx.find("rioxxterms:record_public_release_date", NS))

    def test_preprint_servers_dont_show_them(self):
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        # The record page's own markup; the debug toolbar in test settings
        # can add other text to the page.
        self.assertNotContains(
            self.get(self.preprint.local_url),
            'class="no-bullet list-no-bullet publication-details"',
        )


@freeze_time("2026-11-11 12:00:00")
class MoveImporterFieldsTests(FileAccessTestBase):
    """Migration 0075 moves the old importer's custom fields."""

    def setUp(self):
        super().setUp()
        self.preprint, self.file = self.published_preprint(
            PDF, "aam.pdf", "application/pdf"
        )
        self.licence = sm.Licence.objects.create(
            press=self.press,
            name="Creative Commons Attribution 4.0",
            short_name="CC BY 4.0",
            url="https://creativecommons.org/licenses/by/4.0/",
        )
        names = (
            "Publisher",
            "Source (ISSN/ISBN)",
            "Language",
            "Version",
            "Free to read",
            "Licence",
            "Citation",
            "Related URLs",
            "Contributors / Editors",
        )
        self.fields = {
            name: rm.RepositoryField.objects.create(
                repository=self.repository,
                name=name,
                input_type="text",
                order=i,
                required=False,
            )
            for i, name in enumerate(names)
        }
        answers = {
            "Publisher": "Royal Society",
            "Source (ISSN/ISBN)": "978-0-19-953556-9",
            "Language": "en",
            "Version": "AM",
            "Free to read": "yes",
            "Licence": "https://creativecommons.org/licenses/by/4.0/",
            "Citation": "Bliss, L. (2024) Gravity. Proc B 291.",
            "Related URLs": "https://example.org/press\nhttps://example.org/data",
            "Contributors / Editors": "Editor, E.",
        }
        for name, text in answers.items():
            rm.RepositoryFieldAnswer.objects.create(
                field=self.fields[name], preprint=self.preprint, answer=text
            )

    def run_migration(self):
        module = importlib.import_module(
            "repository.migrations.0075_move_importer_fields"
        )
        module.move_answers(apps, None)

    def test_answers_move_to_their_places_and_the_fields_go(self):
        self.run_migration()
        details = self.preprint.publication_details
        self.assertEqual(details.publisher, "Royal Society")
        self.assertEqual(details.isbn, "978-0-19-953556-9")
        self.assertEqual(details.issn, "")
        self.assertEqual(details.language, "en")
        self.assertIn("Proc B", details.citation)
        self.assertEqual(details.editors, "Editor, E.")
        self.preprint.refresh_from_db()
        self.assertEqual(self.preprint.license, self.licence)
        self.file.refresh_from_db()
        self.assertEqual(self.file.document_version, "accepted")
        self.assertEqual(
            sorted(self.preprint.supplementaryfiles.values_list("url", flat=True)),
            ["https://example.org/data", "https://example.org/press"],
        )
        self.assertFalse(
            rm.RepositoryField.objects.filter(
                repository=self.repository, name__in=list(self.fields)
            ).exists()
        )

    def test_repositories_the_importer_didnt_populate_are_left_alone(self):
        rm.RepositoryField.objects.filter(
            name__in=["Source (ISSN/ISBN)", "Free to read"]
        ).delete()
        self.run_migration()
        self.assertTrue(
            rm.RepositoryField.objects.filter(
                repository=self.repository, name="Publisher"
            ).exists()
        )
        self.assertIsNone(self.preprint.publication_details)
