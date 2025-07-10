# from urllib.parse import unquote_plus
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from django.utils import timezone

from freezegun import freeze_time
from xml.etree import ElementTree as ET

from utils.testing import helpers
from api.tests.test_preprint_oai_data import (
    LIST_RECORDS_DATA_DC,
    LIST_RECORDS_DATA_JATS,
    GET_RECORD_DATA_DC,
    GET_RECORD_DATA_UNTIL,
    GET_RECORD_DATA_JATS,
    LIST_IDENTIFIERS_JATS,
    IDENTIFY_DATA_DC,
    LIST_SETS_DATA_DC,
)

from repository import models as repo_models

REPO_DOMAIN = "repo.domain.com"
FROZEN_DATETIME_202209 = timezone.make_aware(timezone.datetime(2022, 9, 1, 0, 0, 0))
FROZEN_DATETIME_202208 = timezone.make_aware(timezone.datetime(2022, 8, 31, 0, 0, 0))


class TestPreprintOAIViews(TestCase):
    maxDiff = None

    def assertXMLEqual(self, a, b):
        ET.register_namespace('', 'http://www.openarchives.org/OAI/2.0/')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('jats1_0', 'http://www.ncbi.nlm.nih.gov/JATS1') # Crossref uses this
        ET.register_namespace('jats1_2', 'https://jats.nlm.nih.gov/publishing/1.2/') # We use this
        ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
        ET.register_namespace('tk', 'http://oai.dlib.vt.edu/OAI/metadata/toolkit')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        a_element = ET.fromstring(bytes(a, encoding="utf-8"))
        b_element = ET.fromstring(bytes(b, encoding="utf-8"))
        ET.indent(a_element)
        ET.indent(b_element)
        a_new_string = ET.tostring(a_element, encoding="unicode")
        b_new_string = ET.tostring(b_element, encoding="unicode")
        return self.assertEqual(a_new_string, b_new_string)

    @classmethod
    @freeze_time(FROZEN_DATETIME_202208)
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo, cls.subject = helpers.create_repository(cls.press, [], [])

        cls.author = helpers.create_user("preprintauthor@test.edu")
        cls.author.first_name = "Preprint"
        cls.author.last_name = "Author"
        cls.author.save()

        cls.preprint = helpers.create_preprint(cls.repo, cls.author, cls.subject)
        cls.preprint.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.make_aware(
            timezone.datetime(2022, 8, 31, 0, 0, 0)
        )
        cls.preprint.make_new_version(cls.preprint.submission_file)
        cls.preprint.save()

        cls.unpublished_preprint = helpers.create_preprint(
            cls.repo, cls.author, cls.subject, title="Unpublished Preprint"
        )

        cls.older_preprint = helpers.create_preprint(
            cls.repo, cls.author, cls.subject, title="Older Test Preprint"
        )
        cls.older_preprint.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.older_preprint.date_published = timezone.make_aware(
            timezone.datetime(2022, 8, 29, 0, 0, 0)
        )
        cls.older_preprint.make_new_version(cls.older_preprint.submission_file)
        cls.older_preprint.save()

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_list_records_dc(self):
        expected = LIST_RECORDS_DATA_DC
        response = self.client.get(reverse("OAI_list_records"), SERVER_NAME=REPO_DOMAIN)
        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_list_records_jats(self):
        expected = LIST_RECORDS_DATA_JATS
        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)
        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME=REPO_DOMAIN
        )

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_list_sets(self):
        expected = LIST_SETS_DATA_DC

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListSets",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(f"{path}?{query_string}", SERVER_NAME=REPO_DOMAIN)

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_get_record_dc(self):
        expected = GET_RECORD_DATA_DC

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="oai_dc",
            identifier="oai:testrepo:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f"{path}?{query_string}", SERVER_NAME="repo.domain.com"
        )

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_get_record_jats(self):
        expected = GET_RECORD_DATA_JATS

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="jats",
            identifier="oai:testrepo:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f"{path}?{query_string}", SERVER_NAME="repo.domain.com"
        )

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_list_identifiers_jats(self):
        expected = LIST_IDENTIFIERS_JATS

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListIdentifiers",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f"{path}?{query_string}", SERVER_NAME="repo.domain.com"
        )

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_identify_dc(self):
        expected = IDENTIFY_DATA_DC

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="Identify",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f"{path}?{query_string}", SERVER_NAME="repo.domain.com"
        )

        self.assertXMLEqual(expected, response.content.decode())

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME_202209)
    def test_get_records_until(self):
        expected = GET_RECORD_DATA_UNTIL

        path = reverse("OAI_list_records")
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="oai_dc",
            # until=str(datetime.datetime(2022, 8, 30, tzinfo=pytz.UTC)),
            until=timezone.make_aware(timezone.datetime(2022, 8, 30, 0, 0, 0)),
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f"{path}?{query_string}", SERVER_NAME="repo.domain.com"
        )

        self.assertXMLEqual(expected, response.content.decode())
