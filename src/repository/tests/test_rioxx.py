from xml.etree import ElementTree as ET

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from freezegun import freeze_time

from repository import models as rm
from submission import models as sm
from repository.tests.test_file_access import PDF, FileAccessTestBase

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "rioxx": "http://www.rioxx.net/schema/v3.0/rioxx/",
    "ali": "http://ali.niso.org/2014/ali/1.0",
    "dc": "http://purl.org/dc/elements/1.1/",
    "rioxxterms": "http://www.rioxx.net/schema/v3.0/rioxxterms/",
}


@freeze_time("2026-11-11 12:00:00")
@override_settings(URL_CONFIG="domain")
class RioxxTests(FileAccessTestBase):
    def setUp(self):
        super().setUp()
        self.preprint, self.file = self.published_preprint(
            PDF, "aam.pdf", "application/pdf"
        )
        self.preprint.submission_type = rm.RepositorySubmissionType.objects.create(
            repository=self.repository,
            name="Article",
            name_plural="Articles",
            slug="article",
        )
        self.preprint.save()
        self.file.document_version = rm.PreprintFile.VERSION_ACCEPTED
        self.file.save(update_fields=["document_version"])
        sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="Ada",
            last_name="Author",
            frozen_orcid="0000-0002-1825-0097",
            order=0,
        )

    def oai(self, **params):
        return self.client.get(
            "{}?{}".format(reverse("OAI_list_records"), urlencode(params)),
            SERVER_NAME=self.repository.domain,
        )

    def record(self):
        response = self.oai(
            verb="GetRecord",
            metadataPrefix="rioxx",
            identifier="oai:{}:id:{}".format(
                self.repository.short_name, self.preprint.pk
            ),
        )
        self.assertEqual(response.status_code, 200)
        root = ET.fromstring(response.content)
        return root.find(".//rioxx:rioxx", NS)

    def test_institutional_repositories_list_rioxx(self):
        self.assertContains(
            self.oai(verb="ListMetadataFormats"),
            "<metadataPrefix>rioxx</metadataPrefix>",
        )
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        self.assertNotContains(self.oai(verb="ListMetadataFormats"), "rioxx")

    def test_an_open_accepted_manuscript(self):
        rioxx = self.record()
        self.assertIsNotNone(rioxx)
        free = rioxx.find("ali:free_to_read", NS)
        self.assertIsNotNone(free)
        self.assertIsNone(free.get("start_date"))
        self.assertTrue(
            rioxx.find("dc:identifier", NS).text.endswith(self.file.download_url())
        )
        self.assertEqual(rioxx.find("rioxxterms:version", NS).text, "AM")
        self.assertEqual(
            rioxx.find("rioxxterms:type", NS).text,
            "http://purl.org/coar/resource_type/c_6501",
        )
        author = rioxx.find("rioxxterms:author", NS)
        self.assertEqual(author.get("id"), "https://orcid.org/0000-0002-1825-0097")
        self.assertEqual(author.get("first-named-author"), "true")
        self.assertEqual(rioxx.find("dc:language", NS).text, "en")

    def test_an_embargo_gives_the_start_dates(self):
        self.lock(self.file, until="2027-01-01")
        self.preprint.license = sm.Licence.objects.create(
            press=self.press,
            name="CC BY",
            short_name="CC BY 4.0",
            url="https://creativecommons.org/licenses/by/4.0/",
        )
        self.preprint.save()
        rioxx = self.record()
        self.assertEqual(
            rioxx.find("ali:free_to_read", NS).get("start_date"), "2027-01-01"
        )
        self.assertEqual(
            rioxx.find("ali:license_ref", NS).get("start_date"), "2027-01-01"
        )

    def test_a_restricted_file_is_not_free_to_read_or_linked(self):
        self.lock(self.file, rm.PreprintFile.ACCESS_RESTRICTED, until=None)
        rioxx = self.record()
        self.assertIsNone(rioxx.find("ali:free_to_read", NS))
        identifier = rioxx.find("dc:identifier", NS).text
        self.assertNotIn(self.file.download_url(), identifier)
        self.assertTrue(identifier.endswith(self.preprint.local_url))

    def test_list_records_in_rioxx(self):
        response = self.oai(verb="ListRecords", metadataPrefix="rioxx")
        root = ET.fromstring(response.content)
        titles = [t.text for t in root.findall(".//rioxx:rioxx/dc:title", NS)]
        self.assertIn(self.preprint.title, titles)
