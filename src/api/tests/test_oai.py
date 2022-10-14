__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from urllib.parse import unquote_plus
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from freezegun import freeze_time
from lxml import etree

from api.oai.base import OAIPaginationMixin
from submission import models as sm_models
from utils.testing import helpers


class TestOAIViews(TestCase):

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
        cls.issue = helpers.create_issue(
            journal=cls.journal, vol=1, number=1,
            articles=[cls.article],
        )
        cls.issue_2= helpers.create_issue(
            journal=cls.journal, vol=1, number=2,
            articles=[cls.article],
        )
        cls.article.primary_issue = cls.issue
        cls.article.save()

    @classmethod
    def validate_oai_schema(cls, xml):
        xml_schema = etree.XMLSchema(
            "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
        )
        xml_dom = etree.XML(xml)
        return xml_schema.validate(xml_dom)


    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_list_records_dc(self):
        expected = LIST_RECORDS_DATA_DC
        response = self.client.get(reverse('OAI_list_records'), SERVER_NAME="testserver")
        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_list_records_jats(self):
        expected = LIST_RECORDS_DATA_JATS
        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)
        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )
        result = str(response.rendered_content)
        self.assertEqual(result.split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_get_record_dc(self):
        expected = GET_RECORD_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="oai_dc",
            identifier="oai:TST:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("1976-01-02")
    def test_get_records_until(self):
        expected = GET_RECORD_DATA_UNTIL

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="oai_dc",
            until="1976-01-02",
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
        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_get_record_jats(self):
        expected = GET_RECORD_DATA_JATS

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="jats",
            identifier="oai:TST:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_get_record_jats(self):
        expected = LIST_IDENTIFIERS_JATS

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListIdentifiers",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_identify_dc(self):
        expected = IDENTIFY_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="Identify",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )
        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2012-01-14")
    def test_list_sets(self):
        expected = LIST_SETS_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListSets",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )
        result = str(response.rendered_content)

        self.assertEqual(result.split(), expected.split())

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
            request.GET.get("custom-param"), expected["custom-param"],
            "Parameters not being encoded by resumptionToken correctly",
        )

    @override_settings(URL_CONFIG="domain")
    @freeze_time("1990-01-01")
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

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
            **custom_param,
        )
        query_string = urlencode(query_params)
        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="testserver"
        )
        self.assertTrue(
            expected_encoded in unquote_plus(response.context["resumption_token"]),
            "Query parameter has not been encoded into resumption_token",
        )


LIST_RECORDS_DATA_DC = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="ListRecords" metadataPrefix="oai_dc">http://testserver/api/oai/</request>
    <ListRecords>
        <record>
        <header>
    <identifier>oai:TST:id:1</identifier>
    <datestamp>1986-07-12T15:00:00Z</datestamp>
    </header>
        <metadata>
    <oai_dc:dc
        xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
        http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
        <dc:articleTitle>A Test Article</dc:articleTitle>
        <dc:title>A Test Article</dc:title>
        <dc:creator>User, Author A</dc:creator>
        <dc:description>A Test article abstract</dc:description>
        <dc:date>1986-07-12T15:00:00Z</dc:date>
        <dc:type>info:eu-repo/semantics/article</dc:type>
        <dc:volume>1</dc:volume>
        <dc:issue>1</dc:issue>
        <dc:publisher>Press</dc:publisher>
        <dc:journalTitle>Journal One</dc:journalTitle>
        <dc:identifier>http://testserver/article/id/1/</dc:identifier>
        <dc:fullTextUrl>http://testserver/article/id/1/</dc:fullTextUrl>
        <dc:source>0000-0000</dc:source>
        <dc:format.extent>1</dc:format.extent>
    </oai_dc:dc>
        </metadata>
    </record>
    </ListRecords>
    </OAI-PMH>
"""


LIST_RECORDS_DATA_JATS = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="ListRecords" metadataPrefix="jats">http://testserver/api/oai/</request>
    <ListRecords>
        <record>
        <header>
    <identifier>oai:TST:id:1</identifier>
    <datestamp>1986-07-12T15:00:00Z</datestamp>
    </header>
        <metadata>
    <article article-type="research-article" dtd-version="1.0" xml:lang="en" xmlns="https://jats.nlm.nih.gov/publishing/1.2/" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <front>
            <journal-meta>
                <journal-id journal-id-type="issn">0000-0000</journal-id>
                <journal-title-group>
                    <journal-title>Journal One</journal-title>
                </journal-title-group>
                <issn pub-type="epub">0000-0000</issn>
                <publisher>
                    <publisher-name></publisher-name>
                </publisher>
            </journal-meta>
            <article-meta>
                <article-id pub-id-type="publisher-id">1</article-id>
                <article-categories>
                    <subj-group>
                        <subject>Article</subject>
                    </subj-group>
                </article-categories>
                <title-group>
                    <article-title>A Test Article</article-title>
                </title-group>
                <contrib-group>
                    <contrib contrib-type="author">
                        <name>
                            <surname>User</surname>
                            <given-names>Author A</given-names>
                        </name>
                        <email>authoruser@martineve.com</email>
                        <xref ref-type="aff" rid="aff-1"/>
                    </contrib>
                </contrib-group>
                <aff id="aff-1">Author Department, Author institution</aff>
                <pub-date date-type="pub" iso-8601-date="1986-07-12" publication-format="electronic">
                    <day>12</day>
                    <month>07</month>
                    <year>1986</year>
                </pub-date>
                <volume seq="0">1</volume>
                <issue>1</issue>
                <issue-id>1</issue-id>
                <permissions>
                    <copyright-statement>Copyright: © 1986 The Author(s)</copyright-statement>
                    <copyright-year>1986</copyright-year>
                </permissions>
                <self-uri content-type="text/html" xlink:href="http://testserver/article/id/1/"/>
                <abstract>A Test article abstract</abstract>
            </article-meta>
        </front>
    </article>
        </metadata>
    </record>
    </ListRecords>
    </OAI-PMH>
"""


GET_RECORD_DATA_DC = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="GetRecord" metadataPrefix="oai_dc">http://testserver/api/oai/</request>

    <GetRecord>
        <record>

        <header>
    <identifier>oai:TST:id:1</identifier>
    <datestamp>1986-07-12T15:00:00Z</datestamp>
    </header>
        <metadata>
    <oai_dc:dc
        xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
        http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
        <dc:articleTitle>A Test Article</dc:articleTitle>
        <dc:title>A Test Article</dc:title>
        <dc:creator>User, Author A</dc:creator>
        <dc:description>A Test article abstract</dc:description>
        <dc:date>1986-07-12T15:00:00Z</dc:date>
        <dc:type>info:eu-repo/semantics/article</dc:type>
        <dc:volume>1</dc:volume>
        <dc:issue>1</dc:issue>
        <dc:publisher>Press</dc:publisher>
        <dc:journalTitle>Journal One</dc:journalTitle>
        <dc:identifier>http://testserver/article/id/1/</dc:identifier>
        <dc:fullTextUrl>http://testserver/article/id/1/</dc:fullTextUrl>
        <dc:source>0000-0000</dc:source>
        <dc:format.extent>1</dc:format.extent>
    </oai_dc:dc>
        </metadata>
    </record>
    </GetRecord>
    </OAI-PMH>
"""
GET_RECORD_DATA_UNTIL = """
<?xml version="1.0" encoding="UTF-8"?>
 <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
    http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
 <responseDate>1976-01-02T00:00:00Z</responseDate>
  <request verb="ListRecords" metadataPrefix="oai_dc">http://testserver/api/oai/</request>
<ListRecords>
<record>
  <header>
  <identifier>oai:TST:id:2</identifier>
  <datestamp>1975-01-01T15:00:00Z</datestamp>
</header>
    <metadata>
  <oai_dc:dc
      xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
      http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
      <dc:articleTitle>A Test Article</dc:articleTitle>
      <dc:title>A Test Article</dc:title>
      <dc:creator>User, Author A</dc:creator>
      <dc:description>A Test article abstract</dc:description>
      <dc:date>1975-01-01T15:00:00Z</dc:date>
      <dc:type>info:eu-repo/semantics/article</dc:type>
      <dc:publisher>Press</dc:publisher>
      <dc:journalTitle>Journal One</dc:journalTitle>
      <dc:identifier>http://testserver/article/id/2/</dc:identifier>
      <dc:fullTextUrl>http://testserver/article/id/2/</dc:fullTextUrl>
      <dc:source>0000-0000</dc:source>
      <dc:format.extent>1</dc:format.extent>
  </oai_dc:dc>
    </metadata>
</record>
</ListRecords>
</OAI-PMH>
"""


GET_RECORD_DATA_JATS = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="GetRecord" metadataPrefix="jats">http://testserver/api/oai/</request>
    <GetRecord>
            <record>
        <header>
    <identifier>oai:TST:id:1</identifier>
    <datestamp>1986-07-12T15:00:00Z</datestamp>
    </header>
        <metadata>
    <article article-type="research-article" dtd-version="1.0" xml:lang="en" xmlns="https://jats.nlm.nih.gov/publishing/1.2/" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <front>
            <journal-meta>
                <journal-id journal-id-type="issn">0000-0000</journal-id>
                <journal-title-group>
                    <journal-title>Journal One</journal-title>
                </journal-title-group1986-07-12T15:00:00Z>
                <issn pub-type="epub">0000-0000</issn>
                <publisher>
                    <publisher-name></publisher-name>
                </publisher>
            </journal-meta>
            <article-meta>
                <article-id pub-id-type="publisher-id">1</article-id>
                <article-categories>
                    <subj-group>
                        <subject>Article</subject>
                    </subj-group>
                </article-categories>
                <title-group>
                    <article-title>A Test Article</article-title>
                </title-group>
                <contrib-group>
                    <contrib contrib-type="author">
                        <name>
                            <surname>User</surname>
                            <given-names>Author A</given-names>
                        </name>
                        <email>authoruser@martineve.com</email>
                        <xref ref-type="aff" rid="aff-1"/>
                    </contrib>
                </contrib-group>
                <aff id="aff-1">Author Department, Author institution</aff>
                <pub-date date-type="pub" iso-8601-date="1986-07-12" publication-format="electronic">
                    <day>12</day>
                    <month>07</month>
                    <year>1986</year>
                </pub-date>
                <volume seq="0">1</volume>
                <issue>1</issue>
                <issue-id>1</issue-id>
                <permissions>
                    <copyright-statement>Copyright: © 1986 The Author(s)</copyright-statement>
                    <copyright-year>1986</copyright-year>
                </permissions>
                <self-uri content-type="text/html" xlink:href="http://testserver/article/id/1/"/>
                <abstract>A Test article abstract</abstract>
            </article-meta>
        </front>
    </article>
        </metadata>
    </record>
    </GetRecord>
    </OAI-PMH>
"""

LIST_IDENTIFIERS_JATS = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="ListIdentifiers" metadataPrefix="jats">http://testserver/api/oai/</request>
    <ListIdentifiers>
        <header>
    <identifier>oai:TST:id:1</identifier>
    <datestamp>1986-07-12T15:00:00Z</datestamp>
    </header>
    </ListIdentifiers>

    </OAI-PMH>
"""

IDENTIFY_DATA_DC = """
<?xml version="1.0" encoding="UTF-8"?>
 <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
    http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
 <responseDate>2012-01-14T00:00:00Z</responseDate>
  <request verb="Identify" metadataPrefix="oai_dc">http://testserver/api/oai/</request>

    <Identify>
        <repositoryName></repositoryName>
        <baseURL>http://testserver/api/oai/</baseURL>
        <protocolVersion>2.0</protocolVersion>
        <adminEmail>a@b.com</adminEmail>
        <earliestDatestamp>1986-07-12T15:00:00Z</earliestDatestamp>
        <deletedRecord>no</deletedRecord>
        <granularity>YYYY-MM-DDThh:mm:ssZ</granularity>
        <description>
            <toolkit
                    xmlns="http://oai.dlib.vt.edu/OAI/metadata/toolkit"
                    xsi:schemaLocation="http://oai.dlib.vt.edu/OAI/metadata/toolkit
                                        http://oai.dlib.vt.edu/OAI/metadata/toolkit.xsd">
                <title>Janeway</title>
                <author>
                    <name>Birkbeck, University of London</name>
                    <email>olh-tech@bbk.ac.uk</email>
                </author>
                <version></version>
                <URL>http://janeway.systems/</URL>
            </toolkit>
        </description>
    </Identify>

</OAI-PMH>
"""

LIST_SETS_DATA_DC = """
<?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2012-01-14T00:00:00Z</responseDate>
    <request verb="ListSets" metadataPrefix="oai_dc">http://testserver/api/oai/</request>

        <ListSets>

                <set>
                    <setSpec>TST</setSpec>
                    <setName>Journal One</setName>
                </set>


                <set>
                    <setSpec>TST:issue:1</setSpec>
                    <setName>Volume 1 Issue 1 2022 Test Issue from Utils Testing Helpers</setName>
                </set>

                <set>
                    <setSpec>TST:issue:2</setSpec>
                    <setName>Volume 1 Issue 2 2022 Test Issue from Utils Testing Helpers</setName>
                </set>


                <set>
                    <setSpec>TST:section:1</setSpec>
                    <setName>Article</setName>
                </set>

        </ListSets>

    </OAI-PMH>
"""
