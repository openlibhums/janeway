__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from urllib.parse import unquote_plus
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from django.utils import timezone

from freezegun import freeze_time
from xml.etree import ElementTree as ET

from api.oai.base import OAIPaginationMixin
from api.tests.test_oai_data import (
    LIST_RECORDS_DATA_DC,
    LIST_RECORDS_DATA_JATS,
    GET_RECORD_DATA_DC,
    GET_RECORD_DATA_UNTIL,
    GET_RECORD_DATA_JATS,
    LIST_IDENTIFIERS_JATS,
    IDENTIFY_DATA_DC,
    LIST_SETS_DATA_DC,
)
from submission import models as sm_models
from utils.testing import helpers
from utils import setting_handler
from utils.upgrade import shared

FROZEN_DATETIME_2012 = timezone.make_aware(timezone.datetime(2012, 1, 14, 0, 0, 0))
FROZEN_DATETIME_1990 = timezone.make_aware(timezone.datetime(1990, 1, 1, 0, 0, 0))
FROZEN_DATETIME_1976 = timezone.make_aware(timezone.datetime(1976, 1, 2, 0, 0, 0))


class TestOAIViews(TestCase):
    maxDiff = None

    def assertXMLEqual(self, a, b):
        ET.register_namespace("", "http://www.openarchives.org/OAI/2.0/")
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace(
            "jats1_0", "http://www.ncbi.nlm.nih.gov/JATS1"
        )  # Crossref uses this
        ET.register_namespace(
            "jats1_2", "https://jats.nlm.nih.gov/publishing/1.2/"
        )  # We use this
        ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
        ET.register_namespace("oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc/")
        ET.register_namespace("tk", "http://oai.dlib.vt.edu/OAI/metadata/toolkit")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        a_element = ET.fromstring(bytes(a, encoding="utf-8"))
        b_element = ET.fromstring(bytes(b, encoding="utf-8"))
        ET.indent(a_element)
        ET.indent(b_element)
        a_new_string = ET.tostring(a_element, encoding="unicode")
        b_new_string = ET.tostring(b_element, encoding="unicode")
        return self.assertEqual(a_new_string, b_new_string)

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        cls.author = helpers.create_author(cls.journal)
        cls.article = helpers.create_submission(
            journal_id=cls.journal.pk,
            stage=sm_models.STAGE_PUBLISHED,
            date_published="1986-07-12T17:00:00.000+0200",
            authors=[cls.author],
        )
        cls.article.correspondence_author = cls.author
        cls.frozen_author = cls.author.frozen_author(cls.article)
        cls.frozen_author.add_credit("data-curation")
        cls.frozen_author.add_credit("writing-original-draft")
        cls.issue = helpers.create_issue(
            journal=cls.journal,
            vol=1,
            number=1,
            articles=[cls.article],
        )
        cls.issue_2 = helpers.create_issue(
            journal=cls.journal,
            vol=1,
            number=2,
            articles=[cls.article],
        )
        cls.article.primary_issue = cls.issue
        cls.article.save()

    @classmethod
    def validate_oai_schema(cls, xml):
        xml_schema = ET.XMLSchema("http://www.openarchives.org/OAI/2.0/oai_dc.xsd")
        xml_dom = ET.XML(xml)
        return xml_schema.validate(xml_dom)

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_list_records_dc(self):
        expected = LIST_RECORDS_DATA_DC
        response = self.client.get(
            reverse("OAI_list_records"), SERVER_NAME="testserver"
        )
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_list_records_jats(self):
        expected = LIST_RECORDS_DATA_JATS
        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)
        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_get_record_dc(self):
        expected = GET_RECORD_DATA_DC

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="oai_dc",
            identifier="oai:TST:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_1976)
    def test_get_records_until(self):
        expected = GET_RECORD_DATA_UNTIL

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="oai_dc",
            until=timezone.make_aware(timezone.datetime(1976, 1, 2, 0, 0, 0)),
        )
        query_string = urlencode(query_params)

        # Create article that will be returned
        helpers.create_submission(
            journal_id=self.journal.pk,
            stage=sm_models.STAGE_PUBLISHED,
            date_published="1975-01-01T17:00:00.000+0200",
            authors=[self.author],
        )

        # Create article that will not be returned
        helpers.create_submission(
            journal_id=self.journal.pk,
            stage=sm_models.STAGE_PUBLISHED,
            date_published="1977-01-01T17:00:00.000+0200",
            authors=[self.author],
        )
        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_get_record_jats(self):
        expected = GET_RECORD_DATA_JATS
        # Add a non correspondence author
        author_2 = helpers.create_author(self.journal, email="no@email.com")
        author_2.snapshot_as_author(self.article)

        setting_handler.save_setting(
            "general",
            "use_credit",
            journal=self.journal,
            value="on",
        )
        path = reverse("OAI_list_records")
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="jats",
            identifier="oai:TST:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_list_identifiers_jats(self):
        expected = LIST_IDENTIFIERS_JATS

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListIdentifiers",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_identify_dc(self):
        expected = IDENTIFY_DATA_DC.format(
            janeway_version=shared.current_version().number,
        )

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="Identify",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_2012)
    def test_list_sets(self):
        section = sm_models.Section.objects.get(
            journal__code=self.journal.code,
            name="Article",
        )
        expected = LIST_SETS_DATA_DC.format(
            journal_code=self.journal.code,
            journal_name=self.journal.name,
            section_name=section.name,
            section_id=section.pk,
            issue_one_id=self.issue.pk,
            issue_one_title=self.issue.non_pretty_issue_identifier,
            issue_two_id=self.issue_2.pk,
            issue_two_title=self.issue_2.non_pretty_issue_identifier,
        )

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListSets",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    def test_oai_resumption_token_decode(self):
        expected = {"custom-param": "custom-value"}
        encoded = {"resumptionToken": urlencode(expected)}

        class TestView(OAIPaginationMixin):
            pass

        query_params = dict(
            verb="ListRecords",
            **encoded,
        )
        request = RequestFactory().get("/api/oai", query_params)
        TestView.as_view()(request)
        self.assertEqual(
            request.GET.get("custom-param"),
            expected["custom-param"],
            "Parameters not being encoded by resumptionToken correctly",
        )

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_1990)
    def test_oai_resumption_token_encode(self):
        custom_param = {"custom-param": "custom-value"}
        expected = {
            "metadataPrefix": "jats",
            "custom-param": "custom-value",
            "page": 2,
        }
        expected_encoded = urlencode(expected)
        for i in range(1, 102):
            helpers.create_submission(
                journal_id=self.journal.pk,
                stage=sm_models.STAGE_PUBLISHED,
                date_published="1986-07-12T17:00:00.000+0200",
                authors=[self.author],
            )

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
            **custom_param,
        )
        query_string = urlencode(query_params)
        response = self.client.get(f"{path}?{query_string}", SERVER_NAME="testserver")
        self.assertTrue(
            expected_encoded in unquote_plus(response.context["resumption_token"]),
            "Query parameter has not been encoded into resumption_token",
        )
